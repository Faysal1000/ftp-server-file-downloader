from __future__ import annotations

import json
import os
import platform
import queue
import shutil
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from flask import Flask, Response, jsonify, request, send_from_directory

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app import (  # noqa: E402
    DEFAULT_USER_AGENT,
    DirectoryScanner,
    RemoteFile,
    ScannerOptions,
    content_length_from_headers,
    content_range_total,
    readable_size,
    request_timeout,
    safe_local_path,
)


APP_NAME = "File Downloader by Faysal"
APP_DATA_DIR = Path.home() / ".file_downloader_by_faysal"
CONFIG_PATH = APP_DATA_DIR / "config.json"
HISTORY_PATH = APP_DATA_DIR / "history.json"

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"

VERSION_PATH = BASE_DIR / "version.json"
try:
    with open(VERSION_PATH, "r", encoding="utf-8") as f:
        APP_VERSION = json.load(f).get("version", "1.0.0").strip()
except Exception:
    APP_VERSION = "1.0.0"

app = Flask(__name__, static_folder=str(FRONTEND_DIR))


DEFAULT_CONFIG: dict[str, Any] = {
    "download_folder": "~/Downloads/File Downloader by Faysal Downloads",
    "overwrite_files": False,
    "resume_broken": True,
    "skip_completed": True,
    "auto_close": False,
    "preserve_structure": True,
    "max_concurrent": 1,
    "timeout": 30,
    "chunk_size": 8 * 1024 * 1024,
    "retry_failed": True,
    "max_retries": 3,
    "user_agent": DEFAULT_USER_AGENT,
    "rate_limit": 0,
    "ask_sizes": True,
    "max_depth": 10,
    "file_filter": "*",
    "exclude_pattern": "",
    "notify_complete": True,
    "sound_alert": True,
    "notify_error": True,
    "theme": "dark",
    "appearance_preset": "violet",
    "accent_color": "#6c5ce7",
    "font_size": "medium",
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_data_files() -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG.copy())
    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text("[]", encoding="utf-8")


def load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def load_config() -> dict[str, Any]:
    ensure_data_files()
    data = load_json(CONFIG_PATH, {})
    config = DEFAULT_CONFIG.copy()
    if isinstance(data, dict):
        config.update(data)
    config["max_concurrent"] = max(1, min(10, int(config.get("max_concurrent") or 1)))
    config["timeout"] = max(3, int(config.get("timeout") or 30))
    config["chunk_size"] = int(config.get("chunk_size") or DEFAULT_CONFIG["chunk_size"])
    config["max_retries"] = max(0, int(config.get("max_retries") or 0))
    config["max_depth"] = max(0, int(config.get("max_depth") or 10))
    config["rate_limit"] = max(0, float(config.get("rate_limit") or 0))
    return config


def save_config(config: dict[str, Any]) -> dict[str, Any]:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    merged = DEFAULT_CONFIG.copy()
    merged.update(config)
    CONFIG_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


def load_history() -> list[dict[str, Any]]:
    ensure_data_files()
    data = load_json(HISTORY_PATH, [])
    return data if isinstance(data, list) else []


def save_history(history: list[dict[str, Any]]) -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history[-200:], indent=2), encoding="utf-8")


def open_path(path: str) -> None:
    expanded = Path(os.path.expanduser(path)).resolve()
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(expanded)])
    elif os.name == "nt":
        os.startfile(str(expanded))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(expanded)])


def expand_user_path(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


def disk_usage_probe(path: Path) -> Path:
    if path.exists() and path.is_dir():
        return path
    if path.exists() and path.is_file():
        return path.parent
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.parent


class EventBroker:
    def __init__(self) -> None:
        self._subscribers: list[queue.Queue[dict[str, Any]]] = []
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue[dict[str, Any]]:
        subscriber: queue.Queue[dict[str, Any]] = queue.Queue()
        with self._lock:
            self._subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: queue.Queue[dict[str, Any]]) -> None:
        with self._lock:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

    def publish(self, event: dict[str, Any]) -> None:
        event.setdefault("time", now_iso())
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            subscriber.put(event)


events = EventBroker()
state_lock = threading.Lock()
scan_stop_event = threading.Event()
download_stop_event = threading.Event()
download_pause_event = threading.Event()
skip_lock = threading.Lock()
skip_file_ids: set[str] = set()

state: dict[str, Any] = {
    "files": {},
    "file_order": [],
    "folders": set(),
    "scanned_url": "",
    "is_scanning": False,
    "is_downloading": False,
    "is_paused": False,
    "download_started_at": None,
    "active_session_id": None,
}


def publish(event_type: str, **payload: Any) -> None:
    events.publish({"type": event_type, **payload})


def log(level: str, message: str) -> None:
    publish("log", level=level, message=message)


def public_state() -> dict[str, Any]:
    with state_lock:
        files = [state["files"][file_id] for file_id in state["file_order"] if file_id in state["files"]]
        return {
            "files": files,
            "folders": sorted(state["folders"]),
            "scanned_url": state["scanned_url"],
            "is_scanning": state["is_scanning"],
            "is_downloading": state["is_downloading"],
            "is_paused": state["is_paused"],
            "active_session_id": state["active_session_id"],
        }


def reset_scan_state(url: str) -> None:
    with state_lock:
        state["files"] = {}
        state["file_order"] = []
        state["folders"] = set()
        state["scanned_url"] = url
        state["is_scanning"] = True
        state["is_downloading"] = False
        state["is_paused"] = False
        state["download_started_at"] = None
        state["active_session_id"] = None


def handle_scan_event(event: dict[str, Any]) -> None:
    event_type = str(event.get("type", ""))
    if event_type == "folder":
        path = str(event.get("path", "")).strip("/")
        with state_lock:
            state["folders"].add(path)
        publish("folder", path=path, name=event.get("name", "Folder"), depth=event.get("depth", 0))
        if path:
            log("SCAN", f"Found folder: {path}/")
    elif event_type == "file":
        file_data = dict(event["file"])  # type: ignore[index]
        with state_lock:
            if file_data["id"] not in state["files"]:
                state["files"][file_data["id"]] = file_data
                state["file_order"].append(file_data["id"])
        publish("file", file=file_data)
    elif event_type == "scan_started":
        log("INFO", f"Inspection started for {event.get('url', '')}")
        publish("scan_started", url=event.get("url", ""))
    elif event_type == "status":
        publish("status", text=event.get("text", ""))
    elif event_type == "server_status":
        publish("server_status", reachable=bool(event.get("reachable")))
    elif event_type == "log":
        log(str(event.get("level", "INFO")), str(event.get("message", "")))
    elif event_type == "scan_done":
        with state_lock:
            state["is_scanning"] = False
            file_count = len(state["file_order"])
            folder_count = len(state["folders"])
            total_size = sum(
                int(file.get("size") or 0) for file in state["files"].values()
            )
        log("SYSTEM", f"Scan complete. Found {file_count} files in {folder_count} folders ({readable_size(total_size)}).")
        publish("scan_done", files=file_count, folders=folder_count, total_size=total_size)
    elif event_type == "scan_cancelled":
        with state_lock:
            state["is_scanning"] = False
        log("WARN", "Inspection stopped by user.")
        publish("scan_cancelled")
    elif event_type == "scan_error":
        with state_lock:
            state["is_scanning"] = False
        message = str(event.get("error", "Unknown scan error"))
        log("ERROR", message)
        publish("scan_error", error=message)


def scan_worker(url: str, config: dict[str, Any]) -> None:
    options = ScannerOptions(
        ask_sizes=bool(config["ask_sizes"]),
        max_depth=int(config["max_depth"]),
        file_filter=str(config["file_filter"]),
        exclude_pattern=str(config["exclude_pattern"]),
        timeout=int(config["timeout"]),
        user_agent=str(config["user_agent"]),
    )
    DirectoryScanner(url, handle_scan_event, scan_stop_event, options).run()


def update_file(file_id: str, **updates: Any) -> None:
    with state_lock:
        file_data = state["files"].get(file_id)
        if not file_data:
            return
        file_data.update(updates)
        payload = dict(file_data)
    publish("file_update", file=payload)


def should_skip_existing(target: Path, size: int | None, config: dict[str, Any]) -> tuple[bool, str]:
    if not target.exists():
        return False, ""
    if config["skip_completed"] and size is not None and target.stat().st_size == size:
        return True, "already complete"
    if config["skip_completed"] and size is None and target.stat().st_size > 0:
        return True, "already exists"
    if not config["overwrite_files"]:
        return True, "existing file kept"
    return False, ""


def file_was_skipped(file_id: str) -> bool:
    with skip_lock:
        return file_id in skip_file_ids


def clear_skip(file_id: str) -> None:
    with skip_lock:
        skip_file_ids.discard(file_id)


def wait_if_paused(file_id: str) -> bool:
    while download_pause_event.is_set():
        if download_stop_event.is_set() or file_was_skipped(file_id):
            return False
        time.sleep(0.2)
    return True


def download_one(file_data: dict[str, Any], config: dict[str, Any]) -> str:
    file_id = str(file_data["id"])
    rel_path = str(file_data["rel_path"])
    remote = RemoteFile(
        id=file_id,
        url=str(file_data["url"]),
        rel_path=rel_path,
        size=file_data.get("size"),
    )
    output_dir = expand_user_path(str(config["download_folder"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    target = safe_local_path(output_dir, rel_path, bool(config["preserve_structure"]))
    target.parent.mkdir(parents=True, exist_ok=True)
    part_file = Path(str(target) + ".part")

    skipped, reason = should_skip_existing(target, remote.size, config)
    if skipped:
        update_file(file_id, status="skipped", progress=100, speed=0)
        log("SKIP", f"Skipped: {rel_path} ({reason})")
        return "skipped"

    update_file(file_id, status="downloading", speed=0)
    publish("download_active", file_id=file_id, rel_path=rel_path)
    log("DOWN", f"Downloading: {rel_path}")

    session = requests.Session()
    session.headers.update({"User-Agent": str(config["user_agent"])})
    rate_limit_bytes = float(config["rate_limit"]) * 1024 * 1024
    chunk_size = int(config["chunk_size"])
    expected_size = remote.size
    attempts = max(1, int(config["max_retries"]) + 1 if config["retry_failed"] else 1)
    last_error: Exception | None = None

    try:
        for attempt in range(1, attempts + 1):
            if download_stop_event.is_set():
                update_file(file_id, status="cancelled", speed=0)
                return "cancelled"
            if file_was_skipped(file_id):
                update_file(file_id, status="skipped", speed=0)
                log("SKIP", f"Skipped: {rel_path} (user requested)")
                return "skipped"

            existing_bytes = part_file.stat().st_size if config["resume_broken"] and part_file.exists() else 0
            headers: dict[str, str] = {}
            mode = "wb"
            if existing_bytes > 0:
                headers["Range"] = f"bytes={existing_bytes}-"
                mode = "ab"

            try:
                start_time = time.monotonic()
                downloaded = existing_bytes
                last_emit = start_time
                bytes_since_emit = 0
                with session.get(remote.url, headers=headers, stream=True, timeout=request_timeout(int(config["timeout"]))) as response:
                    if existing_bytes and response.status_code == 416 and expected_size and existing_bytes == expected_size:
                        break
                    if response.status_code not in {200, 206}:
                        if response.status_code == 416 and existing_bytes > 0:
                            part_file.unlink(missing_ok=True)
                            raise ValueError("Server rejected range request (416). Resetting download.")
                        response.raise_for_status()
                    if existing_bytes and response.status_code != 206:
                        existing_bytes = 0
                        downloaded = 0
                        mode = "wb"

                    # Always trust HTTP response headers over HTML-parsed/approximate remote.size
                    ranged_total = content_range_total(response.headers)
                    content_length = content_length_from_headers(response.headers)
                    if ranged_total is not None:
                        expected_size = ranged_total
                    elif content_length is not None:
                        expected_size = content_length + existing_bytes

                    if expected_size is not None:
                        update_file(file_id, size=expected_size)

                    with part_file.open(mode) as handle:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if not wait_if_paused(file_id):
                                update_file(file_id, status="paused" if download_pause_event.is_set() else "cancelled", speed=0)
                                return "cancelled"
                            if download_stop_event.is_set():
                                update_file(file_id, status="cancelled", speed=0)
                                return "cancelled"
                            if file_was_skipped(file_id):
                                update_file(file_id, status="skipped", speed=0)
                                log("SKIP", f"Skipped: {rel_path} (user requested)")
                                return "skipped"
                            if not chunk:
                                continue

                            handle.write(chunk)
                            downloaded += len(chunk)
                            bytes_since_emit += len(chunk)

                            if rate_limit_bytes > 0:
                                elapsed = max(time.monotonic() - start_time, 0.001)
                                target_elapsed = downloaded / rate_limit_bytes
                                if target_elapsed > elapsed:
                                    time.sleep(min(target_elapsed - elapsed, 0.5))

                            now = time.monotonic()
                            if now - last_emit >= 0.35:
                                speed = bytes_since_emit / max(now - last_emit, 0.001)
                                progress = (downloaded / expected_size * 100) if expected_size else 0
                                update_file(file_id, progress=min(progress, 99.9), speed=speed, downloaded=downloaded)
                                publish(
                                    "download_progress",
                                    file_id=file_id,
                                    rel_path=rel_path,
                                    progress=min(progress, 99.9),
                                    speed=speed,
                                    downloaded=downloaded,
                                    size=expected_size,
                                )
                                last_emit = now
                                bytes_since_emit = 0

                if expected_size is not None and part_file.exists() and part_file.stat().st_size != expected_size:
                    raise IOError(
                        f"Downloaded size mismatch: expected {readable_size(expected_size)}, got {readable_size(part_file.stat().st_size)}"
                    )
                if part_file.exists():
                    if target.exists() and config["overwrite_files"]:
                        target.unlink()
                    shutil.move(str(part_file), str(target))
                update_file(file_id, status="complete", progress=100, speed=0, downloaded=expected_size or target.stat().st_size)
                publish("download_progress", file_id=file_id, rel_path=rel_path, progress=100, speed=0, downloaded=expected_size, size=expected_size)
                log("DOWN", f"Downloaded: {rel_path} ({readable_size(expected_size)})")
                return "complete"
            except Exception as exc:  # noqa: BLE001 - retry per file.
                last_error = exc
                if attempt < attempts and not download_stop_event.is_set() and not file_was_skipped(file_id):
                    log("WARN", f"Retry {attempt}/{attempts - 1} for {rel_path}: {exc}")
                    time.sleep(min(1.0 * attempt, 5.0))
                    continue
                raise
    finally:
        session.close()
        clear_skip(file_id)

    if last_error:
        raise last_error
    return "complete"


def download_runner(files: list[dict[str, Any]], config: dict[str, Any], session_id: str) -> None:
    started = time.monotonic()
    source_url = ""
    with state_lock:
        state["is_downloading"] = True
        state["is_paused"] = False
        state["download_started_at"] = started
        state["active_session_id"] = session_id
        source_url = state["scanned_url"]

    completed = 0
    skipped = 0
    failed = 0
    cancelled = False
    total_size = sum(int(file.get("size") or 0) for file in files)

    try:
        publish("download_started", total=len(files), total_size=total_size, session_id=session_id)
        log("SYSTEM", f"Download session started. {len(files)} files queued.")
        for file_data in files:
            update_file(str(file_data["id"]), status="queued", progress=file_data.get("progress", 0), speed=0)

        pending_files = list(files)
        active_futures = {}

        with ThreadPoolExecutor(max_workers=10) as executor:
            while (pending_files or active_futures) and not download_stop_event.is_set():
                # Clean up completed futures
                done_futures = [f for f in active_futures if f.done()]
                for f in done_futures:
                    file_data = active_futures.pop(f)
                    file_id = str(file_data["id"])
                    rel_path = str(file_data["rel_path"])
                    if download_stop_event.is_set():
                        cancelled = True
                    try:
                        result = f.result()
                        if result == "complete":
                            completed += 1
                        elif result == "skipped":
                            skipped += 1
                        elif result == "cancelled":
                            cancelled = True
                        else:
                            failed += 1
                    except Exception as exc:  # noqa: BLE001 - per-file failure.
                        failed += 1
                        update_file(file_id, status="error", speed=0, error=str(exc))
                        log("ERROR", f"Failed: {rel_path} - {exc}")

                    publish(
                        "download_summary",
                        completed=completed,
                        skipped=skipped,
                        failed=failed,
                        total=len(files),
                        cancelled=cancelled,
                    )
                    if cancelled:
                        download_stop_event.set()

                if download_stop_event.is_set():
                    break

                # Get latest max concurrent setting dynamically
                current_config = load_config()
                current_max = max(1, min(10, int(current_config.get("max_concurrent") or 1)))

                # Submit new files if we have capacity and files are pending
                while len(active_futures) < current_max and pending_files:
                    file_data = pending_files.pop(0)
                    future = executor.submit(download_one, file_data, current_config)
                    active_futures[future] = file_data

                # Wait for any active futures to finish, up to 0.2 seconds
                if active_futures:
                    wait(list(active_futures.keys()), timeout=0.2, return_when=FIRST_COMPLETED)
                else:
                    time.sleep(0.1)

            # If stopped, cancel remaining files
            if download_stop_event.is_set():
                cancelled = True
                for file_data in pending_files:
                    update_file(str(file_data["id"]), status="cancelled", speed=0)
                # Wait for running tasks to stop
                wait(list(active_futures.keys()))
                for f in active_futures:
                    file_data = active_futures[f]
                    file_id = str(file_data["id"])
                    update_file(file_id, status="cancelled", speed=0)

    finally:
        duration = time.monotonic() - started
        with state_lock:
            state["is_downloading"] = False
            state["is_paused"] = False
            state["active_session_id"] = None
        download_pause_event.clear()
        status = "Cancelled" if cancelled else ("Error" if failed else ("Partial" if skipped else "Complete"))
        record = {
            "id": session_id,
            "date": now_iso(),
            "source_url": source_url,
            "output_dir": str(expand_user_path(str(config["download_folder"]))),
            "files_completed": completed,
            "files_skipped": skipped,
            "files_failed": failed,
            "files_total": len(files),
            "total_size": total_size,
            "duration": duration,
            "status": status,
        }
        history = load_history()
        history.append(record)
        save_history(history)
        log("SYSTEM", f"Download {status.lower()}. {completed} completed, {skipped} skipped, {failed} failed.")
        publish("download_done", **record)


@app.route("/")
def index() -> Response:
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/<path:path>")
def static_files(path: str) -> Response:
    return send_from_directory(str(FRONTEND_DIR), path)


@app.route("/api/state")
def api_state() -> Response:
    return jsonify(public_state())


@app.route("/api/config", methods=["GET", "POST"])
def api_config() -> Response:
    if request.method == "GET":
        return jsonify({"config": load_config(), "path": str(CONFIG_PATH)})
    data = request.get_json(silent=True) or {}
    config = save_config(data)
    log("SYSTEM", "Settings saved.")
    publish("config_updated", config=config)
    return jsonify({"config": config, "path": str(CONFIG_PATH)})


@app.route("/api/config/reset", methods=["POST"])
def api_config_reset() -> Response:
    config = save_config(DEFAULT_CONFIG.copy())
    log("SYSTEM", "Settings reset to defaults.")
    publish("config_updated", config=config)
    return jsonify({"config": config})


@app.route("/api/config/open", methods=["POST"])
def api_config_open() -> Response:
    ensure_data_files()
    open_path(str(CONFIG_PATH))
    return jsonify({"status": "opened", "path": str(CONFIG_PATH)})


@app.route("/api/scan", methods=["POST"])
def api_scan() -> Response:
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    if not url:
        return jsonify({"error": "URL required"}), 400

    with state_lock:
        if state["is_scanning"] or state["is_downloading"]:
            return jsonify({"error": "The app is busy."}), 409

    config = load_config()
    scan_stop_event.clear()
    download_stop_event.clear()
    reset_scan_state(url)
    publish("scan_reset", url=url)
    thread = threading.Thread(target=scan_worker, args=(url, config), daemon=True)
    thread.start()
    return jsonify({"status": "started"})


@app.route("/api/scan/stop", methods=["POST"])
def api_scan_stop() -> Response:
    scan_stop_event.set()
    log("WARN", "Stopping inspection after the current request.")
    return jsonify({"status": "stopping"})


@app.route("/api/scan/clear", methods=["POST"])
def api_scan_clear() -> Response:
    with state_lock:
        if state["is_scanning"] or state["is_downloading"]:
            return jsonify({"error": "The app is busy."}), 409
        state["files"] = {}
        state["file_order"] = []
        state["folders"] = set()
        state["scanned_url"] = ""
        state["is_scanning"] = False
        state["is_downloading"] = False
        state["is_paused"] = False
        state["download_started_at"] = None
        state["active_session_id"] = None
    log("SYSTEM", "Inspection cleared.")
    publish("hello", state=public_state())
    return jsonify({"status": "cleared"})


@app.route("/api/download", methods=["POST"])
def api_download() -> Response:
    data = request.get_json(silent=True) or {}
    mode = str(data.get("mode", "selected"))
    requested_ids = [str(item) for item in data.get("ids", [])]

    with state_lock:
        if state["is_scanning"] or state["is_downloading"]:
            return jsonify({"error": "The app is busy."}), 409
        if mode == "all":
            file_ids = list(state["file_order"])
        else:
            file_ids = [file_id for file_id in requested_ids if file_id in state["files"]]
        files = [dict(state["files"][file_id]) for file_id in file_ids if file_id in state["files"]]

    if not files:
        return jsonify({"error": "No files selected."}), 400

    config = load_config()
    output_dir = expand_user_path(str(config["download_folder"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    download_stop_event.clear()
    download_pause_event.clear()
    with skip_lock:
        skip_file_ids.clear()

    session_id = uuid.uuid4().hex[:12]
    thread = threading.Thread(target=download_runner, args=(files, config, session_id), daemon=True)
    thread.start()
    return jsonify({"status": "started", "session_id": session_id, "files": len(files)})


@app.route("/api/download/pause", methods=["POST"])
def api_download_pause() -> Response:
    download_pause_event.set()
    with state_lock:
        state["is_paused"] = True
    publish("download_paused")
    log("WARN", "Download paused.")
    return jsonify({"status": "paused"})


@app.route("/api/download/resume", methods=["POST"])
def api_download_resume() -> Response:
    download_pause_event.clear()
    with state_lock:
        state["is_paused"] = False
    publish("download_resumed")
    log("SYSTEM", "Download resumed.")
    return jsonify({"status": "resumed"})


@app.route("/api/download/cancel", methods=["POST"])
def api_download_cancel() -> Response:
    download_stop_event.set()
    download_pause_event.clear()
    log("WARN", "Cancelling download queue.")
    return jsonify({"status": "cancelling"})


@app.route("/api/download/skip", methods=["POST"])
def api_download_skip() -> Response:
    data = request.get_json(silent=True) or {}
    file_id = str(data.get("id", ""))
    if not file_id:
        return jsonify({"error": "File id required"}), 400
    with skip_lock:
        skip_file_ids.add(file_id)
    log("SKIP", f"Skip requested for file id {file_id}.")
    return jsonify({"status": "skipping"})


@app.route("/api/storage")
def api_storage() -> Response:
    config = load_config()
    raw_path = request.args.get("path") or str(config["download_folder"])
    path = expand_user_path(raw_path)
    usage = shutil.disk_usage(disk_usage_probe(path))
    folder_size = 0
    if path.exists():
        try:
            if path.is_file():
                folder_size = path.stat().st_size
            else:
                for item in path.rglob("*"):
                    if item.is_file():
                        folder_size += item.stat().st_size
        except OSError:
            folder_size = 0
    return jsonify(
        {
            "path": str(path),
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": round((usage.used / usage.total) * 100, 1) if usage.total else 0,
            "folder_size": folder_size,
        }
    )


@app.route("/api/history", methods=["GET", "DELETE"])
def api_history() -> Response:
    if request.method == "DELETE":
        save_history([])
        log("SYSTEM", "Download history cleared.")
        publish("history_updated")
        return jsonify({"history": []})
    return jsonify({"history": list(reversed(load_history()))})


@app.route("/api/history/<record_id>", methods=["DELETE"])
def api_history_delete(record_id: str) -> Response:
    history = [record for record in load_history() if str(record.get("id")) != record_id]
    save_history(history)
    publish("history_updated")
    return jsonify({"history": list(reversed(history))})


@app.route("/api/open_path", methods=["POST"])
def api_open_path() -> Response:
    data = request.get_json(silent=True) or {}
    path = str(data.get("path", ""))
    if not path:
        return jsonify({"error": "Path required"}), 400
    expanded = expand_user_path(path)
    expanded.mkdir(parents=True, exist_ok=True)
    open_path(str(expanded))
    return jsonify({"status": "opened", "path": str(expanded)})


@app.route("/api/system")
def api_system() -> Response:
    config = load_config()
    path = expand_user_path(str(config["download_folder"]))
    usage = shutil.disk_usage(disk_usage_probe(path))
    return jsonify(
        {
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "developer": "Faysal Ahmmed",
            "license": "Personal Use",
            "os": platform.platform(),
            "python": sys.version.split()[0],
            "config_path": str(CONFIG_PATH),
            "download_folder": str(path),
            "disk_free": usage.free,
            "disk_total": usage.total,
        }
    )


@app.route("/api/stream")
def api_stream() -> Response:
    subscriber = events.subscribe()

    def stream() -> Any:
        publish("hello", state=public_state())
        try:
            while True:
                try:
                    event = subscriber.get(timeout=15)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    yield ": keep-alive\n\n"
        finally:
            events.unsubscribe(subscriber)

    return Response(stream(), mimetype="text/event-stream")


ensure_data_files()


if __name__ == "__main__":
    app.run(port=5050, threaded=True, use_reloader=False)
