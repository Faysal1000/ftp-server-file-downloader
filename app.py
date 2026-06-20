#!/usr/bin/env python3
"""
Core scanner utilities for SAMOnline FTP Downloader.

The desktop shell lives in main.py/backend/server.py/frontend/*. This module is
kept UI-free so it can be tested, packaged, and reused by the Flask backend.
"""

from __future__ import annotations

import fnmatch
import hashlib
import posixpath
import re
import threading
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class RemoteFile:
    id: str
    url: str
    rel_path: str
    size: int | None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data.update(
            {
                "type": "file",
                "status": "ready",
                "progress": 0,
                "speed": 0,
                "selected": True,
            }
        )
        return data


@dataclass(frozen=True)
class ScannerOptions:
    ask_sizes: bool = True
    max_depth: int = 10
    file_filter: str = "*"
    exclude_pattern: str = ""
    timeout: int = 30
    user_agent: str = DEFAULT_USER_AGENT


EventCallback = Callable[[dict[str, object]], None]


def make_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if "://" not in url:
        url = "http://" + url
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def ensure_directory_url(url: str) -> str:
    url = normalize_url(url)
    if url and not url.endswith("/"):
        url += "/"
    return url


def same_site(candidate: str, base: str) -> bool:
    cand = urlsplit(candidate)
    root = urlsplit(base)
    return cand.scheme == root.scheme and cand.netloc == root.netloc


def url_path(url: str) -> str:
    return posixpath.normpath(urlsplit(url).path)


def is_under_base(candidate: str, base: str) -> bool:
    if not same_site(candidate, base):
        return False
    base_path = unquote(urlsplit(base).path)
    cand_path = unquote(urlsplit(candidate).path)
    return cand_path == base_path.rstrip("/") or cand_path.startswith(base_path)


def relative_remote_path(candidate: str, base: str, is_dir: bool = False) -> str:
    base_path = unquote(urlsplit(base).path)
    cand_path = unquote(urlsplit(candidate).path)
    if cand_path.startswith(base_path):
        rel = cand_path[len(base_path) :]
    else:
        rel = posixpath.basename(cand_path)
    rel = rel.strip("/")
    if is_dir:
        rel = rel.rstrip("/")
    return rel


def readable_size(num_bytes: int | None) -> str:
    if num_bytes is None or num_bytes < 0:
        return "Unknown"
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if value < 1024 or unit == "PB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


def parse_size_text(text: str) -> int | None:
    text = " ".join(text.replace("\xa0", " ").split())
    if not text or text == "-":
        return None

    unit_pattern = re.compile(
        r"(?<![\w.])(\d+(?:\.\d+)?)\s*(bytes?|[KMGTPE](?:i?B|B)?|B)\b",
        re.IGNORECASE,
    )
    matches = list(unit_pattern.finditer(text))
    if matches:
        number, unit = matches[-1].groups()
        return size_to_bytes(float(number), unit)

    # Plain byte counts are only trusted when they are table cells or trailing
    # listing fields. This avoids treating episode numbers as file sizes.
    plain_match = re.search(r"(?:^|\s)(\d{5,18})\s*$", text)
    if not plain_match:
        return None
    return int(plain_match.group(1))


def size_to_bytes(number: float, unit: str) -> int:
    unit = unit.lower()
    if unit in {"b", "byte", "bytes"}:
        multiplier = 1
    elif unit.startswith("k"):
        multiplier = 1024
    elif unit.startswith("m"):
        multiplier = 1024**2
    elif unit.startswith("g"):
        multiplier = 1024**3
    elif unit.startswith("t"):
        multiplier = 1024**4
    elif unit.startswith("p"):
        multiplier = 1024**5
    else:
        multiplier = 1
    return int(number * multiplier)


def text_from_node(node: object) -> str:
    if hasattr(node, "get_text"):
        return node.get_text(" ", strip=True)
    return str(node)


def size_near_link(anchor: object) -> int | None:
    row = anchor.find_parent("tr")
    if row is not None:
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
        for cell_text in reversed(cells[1:]):
            size = parse_size_text(cell_text)
            if size is not None:
                return size

    following: list[str] = []
    for sibling in anchor.next_siblings:
        if getattr(sibling, "name", None) == "a":
            break
        following.append(text_from_node(sibling))
    return parse_size_text(" ".join(following))


def content_length_from_headers(headers: requests.structures.CaseInsensitiveDict[str]) -> int | None:
    length = headers.get("Content-Length")
    if not length:
        return None
    try:
        return int(length)
    except ValueError:
        return None


def content_range_total(headers: requests.structures.CaseInsensitiveDict[str]) -> int | None:
    content_range = headers.get("Content-Range", "")
    match = re.search(r"/(\d+)\s*$", content_range)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def request_timeout(seconds: int) -> tuple[int, int]:
    seconds = max(3, int(seconds or 30))
    return (min(10, seconds), seconds)


def remote_size(
    session: requests.Session,
    url: str,
    stop_event: threading.Event,
    timeout_seconds: int,
) -> int | None:
    if stop_event.is_set():
        return None
    try:
        response = session.head(url, allow_redirects=True, timeout=request_timeout(timeout_seconds))
        if response.ok:
            length = content_length_from_headers(response.headers)
            if length is not None:
                return length
    except requests.RequestException:
        pass

    if stop_event.is_set():
        return None
    try:
        response = session.get(
            url,
            headers={"Range": "bytes=0-0"},
            stream=True,
            allow_redirects=True,
            timeout=request_timeout(timeout_seconds),
        )
        try:
            total = content_range_total(response.headers)
            if total is not None:
                return total
            return content_length_from_headers(response.headers)
        finally:
            response.close()
    except requests.RequestException:
        return None


def safe_local_path(output_dir: Path, rel_path: str, preserve_structure: bool = True) -> Path:
    root = output_dir.expanduser().resolve()
    parts = PurePosixPath(rel_path).parts if preserve_structure else (PurePosixPath(rel_path).name,)
    target = root.joinpath(*parts).resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"Unsafe remote path: {rel_path}")
    return target


def split_patterns(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def excluded(rel_path: str, patterns: str) -> bool:
    if not patterns:
        return False
    rel_path = rel_path.strip("/")
    name = posixpath.basename(rel_path)
    for pattern in split_patterns(patterns):
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(name, pattern):
            return True
        if pattern.endswith("/") and rel_path.startswith(pattern.rstrip("/")):
            return True
    return False


def allowed_file(rel_path: str, filter_value: str) -> bool:
    filters = split_patterns(filter_value or "*")
    if not filters or "*" in filters:
        return True
    suffix = PurePosixPath(rel_path).suffix.lower().lstrip(".")
    name = posixpath.basename(rel_path).lower()
    for item in filters:
        item = item.lower().strip()
        if not item:
            continue
        if item == "*":
            return True
        if item.startswith("*.") and fnmatch.fnmatch(name, item):
            return True
        if item.startswith(".") and suffix == item.lstrip("."):
            return True
        if suffix == item:
            return True
    return False


class DirectoryScanner:
    def __init__(
        self,
        root_url: str,
        emit: EventCallback,
        stop_event: threading.Event,
        options: ScannerOptions | None = None,
    ) -> None:
        self.root_url = ensure_directory_url(root_url)
        self.emit = emit
        self.stop_event = stop_event
        self.options = options or ScannerOptions()
        self.visited_dirs: set[str] = set()
        self.visited_files: set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.options.user_agent or DEFAULT_USER_AGENT})

    def run(self) -> None:
        try:
            if not self.root_url:
                raise ValueError("Please enter a directory URL.")
            if urlsplit(self.root_url).scheme not in {"http", "https"}:
                raise ValueError("Only HTTP/HTTPS open directory listings are supported.")

            self.emit({"type": "scan_started", "url": self.root_url})
            self.emit({"type": "folder", "path": "", "name": "Root Directory", "depth": 0})
            self.scan_directory(self.root_url, depth=0)

            if self.stop_event.is_set():
                self.emit({"type": "scan_cancelled"})
            else:
                self.emit({"type": "scan_done"})
        except Exception as exc:  # noqa: BLE001 - surfaced through the UI.
            self.emit({"type": "scan_error", "error": str(exc)})
        finally:
            self.session.close()

    def scan_directory(self, url: str, depth: int) -> None:
        if self.stop_event.is_set():
            return
        if depth > max(0, self.options.max_depth):
            self.emit({"type": "log", "level": "WARN", "message": f"Max scan depth reached at {url}"})
            return

        directory_url = ensure_directory_url(url)
        canonical = normalize_url(directory_url)
        if canonical in self.visited_dirs:
            return
        self.visited_dirs.add(canonical)

        rel_dir = relative_remote_path(directory_url, self.root_url, is_dir=True)
        if rel_dir and excluded(rel_dir + "/", self.options.exclude_pattern):
            self.emit({"type": "log", "level": "SCAN", "message": f"Excluded folder: {rel_dir}/"})
            return

        label = rel_dir or "root folder"
        self.emit({"type": "status", "text": f"Scanning: {label}"})
        self.emit({"type": "log", "level": "SCAN", "message": f"Inspecting folder: {label}"})

        try:
            response = self.session.get(directory_url, timeout=request_timeout(self.options.timeout))
            response.raise_for_status()
            if depth == 0:
                self.emit({"type": "server_status", "reachable": True})
        except requests.RequestException as exc:
            if depth == 0:
                self.emit({"type": "server_status", "reachable": False})
            self.emit({"type": "log", "level": "ERROR", "message": f"Could not read {directory_url}: {exc}"})
            return

        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower() and "<a" not in response.text.lower():
            self.emit({"type": "log", "level": "WARN", "message": f"Skipping non-directory response: {directory_url}"})
            return

        soup = BeautifulSoup(response.text, "html.parser")
        entries = list(self.extract_entries(soup, directory_url))
        directories = [entry for entry in entries if entry["is_dir"]]
        files = [entry for entry in entries if not entry["is_dir"]]

        for entry in files:
            if self.stop_event.is_set():
                return
            self.emit_file(entry)

        for entry in directories:
            if self.stop_event.is_set():
                return
            rel_path = relative_remote_path(str(entry["url"]), self.root_url, is_dir=True)
            if rel_path:
                self.emit(
                    {
                        "type": "folder",
                        "path": rel_path,
                        "name": posixpath.basename(rel_path),
                        "depth": depth + 1,
                    }
                )
            self.scan_directory(str(entry["url"]), depth=depth + 1)

    def emit_file(self, entry: dict[str, object]) -> None:
        file_url = str(entry["url"])
        file_key = normalize_url(file_url)
        if file_key in self.visited_files:
            return
        self.visited_files.add(file_key)

        rel_path = relative_remote_path(file_url, self.root_url, is_dir=False)
        if not rel_path:
            return
        if excluded(rel_path, self.options.exclude_pattern) or not allowed_file(rel_path, self.options.file_filter):
            self.emit({"type": "log", "level": "SCAN", "message": f"Filtered out: {rel_path}"})
            return

        size = entry["size"]
        if size is None and self.options.ask_sizes:
            size = remote_size(self.session, file_url, self.stop_event, self.options.timeout)

        remote_file = RemoteFile(id=make_id(file_url), url=file_url, rel_path=rel_path, size=size)
        size_text = readable_size(size)
        self.emit({"type": "file", "file": remote_file.to_dict()})
        self.emit({"type": "log", "level": "SCAN", "message": f"Found file: {rel_path} ({size_text})"})

    def extract_entries(self, soup: BeautifulSoup, current_url: str) -> Iterable[dict[str, object]]:
        for anchor in soup.find_all("a", href=True):
            href = str(anchor.get("href", "")).strip()
            if self.should_skip_href(href, anchor.get_text(" ", strip=True)):
                continue

            candidate = normalize_url(urljoin(current_url, href))
            if not is_under_base(candidate, self.root_url):
                continue
            if url_path(candidate) == url_path(current_url) and not href.endswith("/"):
                continue

            is_dir = urlsplit(candidate).path.endswith("/") or href.endswith("/")
            if is_dir:
                candidate = ensure_directory_url(candidate)

            yield {
                "url": candidate,
                "is_dir": is_dir,
                "size": None if is_dir else size_near_link(anchor),
            }

    @staticmethod
    def should_skip_href(href: str, label: str) -> bool:
        lowered = href.lower()
        label_lower = label.lower().strip()
        if not href or href.startswith("#") or href.startswith("?"):
            return True
        if lowered.startswith(("mailto:", "javascript:", "tel:", "data:")):
            return True
        if href in {"../", "./", "/"}:
            return True
        if label_lower in {"parent directory", "parent folder", "up to parent directory"}:
            return True
        return False
