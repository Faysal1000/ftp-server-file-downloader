import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import requests
import webview

REPO = "Faysal1000/ftp-server-file-downloader"
UPDATE_API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
UPDATE_DOWNLOAD_BASE_URL = f"https://github.com/{REPO}/releases/latest/download"
UPDATE_CHUNK_SIZE = 1024 * 512

def _get_resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent.resolve()
    return str(base_path / relative_path)

def _parse_version_parts(version):
    parts = [int(part) for part in re.findall(r"\d+", version or "")]
    return tuple((parts + [0, 0, 0])[:3])

def _remote_version_is_newer(latest_version, current_version):
    latest_parts = _parse_version_parts(latest_version)
    current_parts = _parse_version_parts(current_version)
    if any(latest_parts) or any(current_parts):
        return latest_parts > current_parts
    return (latest_version or "").strip().lower() != (current_version or "").strip().lower()

def _build_update_info(release_data):
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        if "arm" in machine or "aarch" in machine:
            asset_name = "FTP-Downloader-macOS-AppleSilicon.zip"
        else:
            asset_name = "FTP-Downloader-macOS-Intel.zip"
        package_type = "mac_zip"
    elif system == "Windows":
        asset_name = "FTP-Downloader-Windows.exe"
        package_type = "windows_exe"
    else:
        asset_name = "FTP-Downloader-Linux"
        package_type = "linux_binary"

    download_url = f"{UPDATE_DOWNLOAD_BASE_URL}/{asset_name}"
    for asset in release_data.get("assets", []):
        if asset.get("name") == asset_name and asset.get("browser_download_url"):
            download_url = asset["browser_download_url"]
            break

    return {
        "version": release_data.get("tag_name", "latest"),
        "asset_name": asset_name,
        "download_url": download_url,
        "package_type": package_type,
        "system": system,
    }

def check_for_updates():
    try:
        version_file = _get_resource_path("version.json")
        if not os.path.exists(version_file):
            return {"update_available": False, "error": "version.json not found"}

        with open(version_file, "r") as f:
            data = json.load(f)
            current_version = data.get("version", "v1.0.0").strip()

        response = requests.get(UPDATE_API_URL, timeout=5)
        if response.status_code == 200:
            release_data = response.json()
            latest_tag = release_data.get("tag_name")
            if latest_tag and _remote_version_is_newer(latest_tag, current_version):
                info = _build_update_info(release_data)
                info["update_available"] = True
                info["current_version"] = current_version
                return info
    except Exception as e:
        return {"update_available": False, "error": str(e)}
    
    return {"update_available": False}

def _get_current_app_path():
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).resolve()
        if platform.system() == "Darwin" and ".app/Contents/MacOS" in exe_path.as_posix():
            return exe_path.parents[2]
        return exe_path
    return Path(__file__).resolve()

def _get_update_download_path(update_info):
    updates_dir = Path.home() / ".file_downloader_by_faysal" / "updates"
    updates_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".new" if update_info["package_type"] in {"windows_exe", "linux_binary"} else ".tmp"
    return updates_dir / f"{update_info['asset_name']}{suffix}"

def _format_download_size(byte_count):
    mb_count = byte_count / (1024 * 1024)
    return f"{mb_count:.1f} MB"

update_cancel_event = threading.Event()

def perform_update(update_info):
    update_cancel_event.clear()
    def update_worker():
        window = webview.windows[0] if webview.windows else None
        def set_progress(percent, text):
            if window:
                window.evaluate_js(f"window.updateProgress({percent}, '{text}');")
        
        try:
            download_path = _get_update_download_path(update_info)
            if download_path.exists():
                download_path.unlink()

            downloaded = 0
            last_ui_update = 0

            with requests.get(update_info["download_url"], stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length") or 0)

                with open(download_path, "wb") as file_obj:
                    for chunk in response.iter_content(chunk_size=UPDATE_CHUNK_SIZE):
                        if update_cancel_event.is_set():
                            file_obj.close()
                            if download_path.exists():
                                download_path.unlink()
                            set_progress(-2, "Update cancelled by user.")
                            return
                        if not chunk:
                            continue

                        file_obj.write(chunk)
                        downloaded += len(chunk)

                        now = time.time()
                        if now - last_ui_update < 0.1:
                            continue

                        last_ui_update = now
                        if total_size:
                            progress = min(downloaded / total_size, 1)
                            percent = int(progress * 100)
                            status_text = f"Downloading... {percent}% ({_format_download_size(downloaded)} / {_format_download_size(total_size)})"
                        else:
                            progress = 0
                            status_text = f"Downloading... {_format_download_size(downloaded)}"

                        set_progress(progress * 100, status_text)

            set_progress(100, "Download complete. Installing and restarting...")
            
            # Install
            if not getattr(sys, "frozen", False):
                set_progress(100, "Update skipped: running in development mode.")
                return

            if update_info["package_type"] == "windows_exe":
                _write_and_launch_windows_updater(download_path)
            elif update_info["package_type"] == "mac_zip":
                extract_dir = download_path.parent / "extracted"
                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
                extract_dir.mkdir(parents=True, exist_ok=True)

                unzip_cmd = "/usr/bin/unzip" if Path("/usr/bin/unzip").exists() else "unzip"
                subprocess.run(
                    [unzip_cmd, "-q", "-o", str(download_path), "-d", str(extract_dir)],
                    check=True
                )

                new_app_path = _find_extracted_macos_app(extract_dir)
                if not new_app_path:
                    set_progress(100, "Error: The downloaded macOS archive did not contain a .app bundle.")
                    return

                _ensure_macos_app_executable(new_app_path)
                _write_and_launch_posix_updater(new_app_path, download_path.parent)
            else:
                os.chmod(download_path, os.stat(download_path).st_mode | 0o755)
                _write_and_launch_posix_updater(download_path, download_path.parent)

        except Exception as e:
            set_progress(-1, f"Update failed: {str(e)}")

    threading.Thread(target=update_worker, daemon=True).start()

def _find_extracted_macos_app(extract_dir):
    expected_app = extract_dir / "FTP-Downloader.app"
    if expected_app.exists():
        return expected_app
    for app_path in extract_dir.rglob("*.app"):
        if "__MACOSX" not in app_path.parts:
            return app_path
    return None

def _ensure_macos_app_executable(app_path):
    macos_dir = app_path / "Contents" / "MacOS"
    if not macos_dir.exists():
        return
    for item in macos_dir.iterdir():
        if item.is_file():
            os.chmod(item, os.stat(item).st_mode | 0o755)

def _write_and_launch_windows_updater(new_file_path):
    target_path = _get_current_app_path()
    script_path = new_file_path.parent / "updater.bat"
    backup_path = target_path.with_suffix(target_path.suffix + ".old")

    script = f"""@echo off
setlocal enabledelayedexpansion
set "TARGET={target_path}"
set "NEWFILE={new_file_path}"
set "BACKUP={backup_path}"
set RETRIES=0
timeout /t 2 /nobreak >nul
if exist "%BACKUP%" del /f /q "%BACKUP%" >nul 2>&1
:wait_for_exit
if exist "%TARGET%" (
    move /y "%TARGET%" "%BACKUP%" >nul 2>&1
    if errorlevel 1 (
        set /a RETRIES+=1
        if !RETRIES! GEQ 30 exit /b 1
        timeout /t 1 /nobreak >nul
        goto wait_for_exit
    )
)
move /y "%NEWFILE%" "%TARGET%" >nul
if errorlevel 1 (
    if exist "%BACKUP%" move /y "%BACKUP%" "%TARGET%" >nul
    exit /b 1
)
if exist "%BACKUP%" del /f /q "%BACKUP%" >nul 2>&1
start "" "%TARGET%"
del "%~f0"
"""
    script_path.write_text(script, encoding="utf-8")

    try:
        subprocess.run(["attrib", "+h", str(script_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        pass

    creation_flags = 0
    if hasattr(subprocess, "DETACHED_PROCESS"):
        creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

    subprocess.Popen(["cmd", "/c", str(script_path)], close_fds=True, creationflags=creation_flags)
    _schedule_exit_for_update()

def _write_and_launch_posix_updater(new_item_path, cleanup_dir):
    target_path = _get_current_app_path()
    script_path = cleanup_dir / "updater.sh"

    script = f"""#!/bin/sh
TARGET={shlex.quote(str(target_path))}
NEW_ITEM={shlex.quote(str(new_item_path))}
CLEANUP_DIR={shlex.quote(str(cleanup_dir))}
BACKUP="${{TARGET}}.update-backup"
TRIES=0
sleep 2
rm -rf "$BACKUP"
if [ -e "$TARGET" ]; then
    while ! mv "$TARGET" "$BACKUP" 2>/dev/null; do
        TRIES=$((TRIES + 1))
        if [ "$TRIES" -ge 30 ]; then
            exit 1
        fi
        sleep 1
    done
fi
if mv "$NEW_ITEM" "$TARGET"; then
    rm -rf "$BACKUP"
    if [ -d "$TARGET" ]; then
        xattr -dr com.apple.quarantine "$TARGET" >/dev/null 2>&1
        /usr/bin/open "$TARGET"
    else
        chmod +x "$TARGET" >/dev/null 2>&1
        "$TARGET" >/dev/null 2>&1 &
    fi
    rm -rf "$CLEANUP_DIR"
else
    if [ -e "$BACKUP" ]; then
        mv "$BACKUP" "$TARGET" 2>/dev/null
    fi
fi
"""
    script_path.write_text(script, encoding="utf-8")
    os.chmod(script_path, 0o755)
    subprocess.Popen(["/bin/sh", str(script_path)], close_fds=True)
    _schedule_exit_for_update()

def _schedule_exit_for_update():
    def exit_app():
        time.sleep(1)
        os._exit(0)
    threading.Thread(target=exit_app, daemon=True).start()
