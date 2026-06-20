from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    import requests
    import webview
except ImportError as exc:
    raise SystemExit(
        "Missing desktop dependencies.\n"
        "Install them with:\n"
        "  /opt/miniconda3/bin/conda run -n py312 pip install -r requirements.txt"
    ) from exc

from backend.server import CONFIG_PATH, app as flask_app, ensure_data_files
import updater

def find_free_port(start: int = 5050) -> int:
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("Could not find a free local port.")


def start_server(port: int) -> None:
    flask_app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False)


def wait_for_server(port: int) -> None:
    url = f"http://127.0.0.1:{port}/api/state"
    for _ in range(80):
        try:
            if requests.get(url, timeout=0.5).ok:
                return
        except requests.RequestException:
            time.sleep(0.1)
    raise RuntimeError("The local app server did not start.")


def open_path(path: str) -> None:
    expanded = Path(os.path.expanduser(path)).resolve()
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(expanded)])
    elif os.name == "nt":
        os.startfile(str(expanded))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(expanded)])


class NativeApi:
    def select_folder(self, initial: str | None = None) -> str | None:
        directory = str(Path(os.path.expanduser(initial or "~")).resolve())
        window = webview.windows[0] if webview.windows else None
        if window is None:
            return None
        result = window.create_file_dialog(webview.FOLDER_DIALOG, directory=directory, allow_multiple=False)
        if not result:
            return None
        return str(result[0] if isinstance(result, (list, tuple)) else result)

    def open_path(self, path: str) -> bool:
        Path(os.path.expanduser(path)).mkdir(parents=True, exist_ok=True)
        open_path(path)
        return True

    def open_config(self) -> bool:
        ensure_data_files()
        open_path(str(CONFIG_PATH))
        return True

    def check_for_updates(self):
        return updater.check_for_updates()

    def perform_update(self, update_info):
        updater.perform_update(update_info)
        return True


def main() -> None:
    ensure_data_files()
    port = find_free_port()
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()
    wait_for_server(port)

    webview.create_window(
        "SAMOnline FTP Downloader",
        f"http://127.0.0.1:{port}/",
        js_api=NativeApi(),
        width=1360,
        height=860,
        min_size=(1040, 680),
    )
    webview.start(private_mode=False, debug=False)


if __name__ == "__main__":
    main()
