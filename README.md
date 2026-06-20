# SAMOnline FTP Downloader

A high-performance desktop application for recursively traversing, browsing, and downloading files from HTTP open directory listings. It features a modern, responsive user interface to traverse nested server directories, allowing you to bulk-download folders or specific files while preserving the remote directory structure.

**No coding knowledge required** — download a single file, double-click, and start downloading.

---

## Core Features

- **Automated Recursive Traversal**: Map target URLs and index all child folders and files with custom depth limits.
- **Selective Downloads & File Tree**: Browse directory listings in a native folder tree structure and selectively mark files/directories for download.
- **Real-Time Download Dashboard**: Monitor total size, download speed, ETA, elapsed time, progress metrics, and selected file counts.
- **Dynamic Themes & Accents**: Glassmorphic UI with full support for accent configurations and dynamic appearance presets.
- **System Notification & Sound Bridge**: Native notifications (on complete or error) integrated with OS-level audio playback (`afplay` on macOS, PowerShell on Windows, `aplay`/`paplay` on Linux).
- **Resumable Downloads**: Automatic retry loops for failed downloads, with partial range requests (HTTP 206) for broken transfers.
- **Safe Auto-Updater**: Checks for updates against GitHub Releases on startup, runs extraction in a persistent directory, and supports download cancellation.

---

## Quick Start

Go to the [**Releases**](../../releases/latest) page and download the executable for your operating system:

| Executable | Target Platform |
| :--- | :--- |
| `FTP-Downloader-Windows.exe` | Windows 10/11 (64-bit) |
| `FTP-Downloader-macOS-AppleSilicon.zip` | macOS (M1/M2/M3/M4/M5 Apple Silicon) |
| `FTP-Downloader-Linux` | Linux (Ubuntu, Debian, Fedora, etc.) |

### Fast Shell Installation

**1. Windows**: Paste this into Command Prompt (`cmd`) to download the Windows executable directly to your Desktop:
```cmd
cd "%USERPROFILE%\Desktop" & curl -L -O https://github.com/Faysal1000/ftp-server-file-downloader/releases/latest/download/FTP-Downloader-Windows.exe
```
*(Double-click to run. If Windows SmartScreen warns you, click "More info" → "Run anyway")*

**2. macOS (Apple Silicon)**: Paste this into Terminal to download, unzip, register execution permissions, and bypass Gatekeeper quarantine:
```bash
cd ~/Desktop && curl -L -O https://github.com/Faysal1000/ftp-server-file-downloader/releases/latest/download/FTP-Downloader-macOS-AppleSilicon.zip && unzip -o FTP-Downloader-macOS-AppleSilicon.zip && rm FTP-Downloader-macOS-AppleSilicon.zip && chmod -R +x ~/Desktop/FTP-Downloader.app && xattr -cr ~/Desktop/FTP-Downloader.app
```
*(Double-click the `FTP-Downloader.app` bundle on your Desktop to run)*

**3. Linux**: Paste this into terminal to download and set execution permissions:
```bash
cd ~/Desktop && curl -L -O https://github.com/Faysal1000/ftp-server-file-downloader/releases/latest/download/FTP-Downloader-Linux && chmod +x FTP-Downloader-Linux
```

---

## Project Structure

```
ftp-server-file-downloader/
├── main.py              # Application entry point (WebView shell configuration & Native API Bridge)
├── app.py               # Core directory listing traversal & parsing module
├── updater.py           # Self-updater script (downloads, unzips, and installs in stable directory)
├── version.json         # Single source of truth version file (e.g. v2.0.3)
├── requirements.txt     # Python application dependencies
├── backend/
│   └── server.py        # Flask local WSGI web server endpoints, routing, and download manager
└── frontend/
    ├── index.html       # User interface layout (Stats cards, main panel, settings)
    ├── script.js        # UI logic, state management, SSE client, and audio player bindings
    ├── style.css        # Premium style configurations (Glassmorphism, presets, and theme variants)
    └── assets/
        ├── file_icon.png      # Custom file row icon
        ├── notification.mp3   # Success sound alert
        ├── error.mp3          # Error sound alert
        ├── icon.icns          # macOS packaged application icon
        └── icon.ico           # Windows packaged application icon
```

---

## Architecture Flow

The app operates via a local Flask background server bound to a custom port on `127.0.0.1`, wrapped in a native desktop frame via PyWebView:

```
[PyWebView Desktop Frame]  <---------(HTTP / SSE)--------->  [Local Flask WSGI Server]
         |                                                             |
    (JS API Bridge)                                             (Download Manager)
         |                                                             |
  [Native OS System]                                           [HTTP File Server]
(afplay / display notifications)
```

---

## Developer Guide

### Prerequisites
- Python 3.12+
- Recommended: Conda package manager

### Running Locally

```bash
# Clone the repository
git clone https://github.com/Faysal1000/ftp-server-file-downloader.git
cd ftp-server-file-downloader

# Install project dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Building Packaged Binaries

To package standalone binaries locally using PyInstaller:

**macOS Build**:
```bash
pyinstaller --noconfirm --onedir --windowed --name "FTP-Downloader" --icon "frontend/assets/icon.icns" --add-data "frontend:frontend" --add-data "version.json:." main.py
```

**Windows Build**:
```bash
pyinstaller --noconfirm --onefile --windowed --name "FTP-Downloader" --icon "frontend/assets/icon.ico" --add-data "frontend;frontend" --add-data "version.json;." main.py
```

**Linux Build**:
```bash
pyinstaller --noconfirm --onefile --windowed --name "FTP-Downloader" --add-data "frontend:frontend" --add-data "version.json:." main.py
```

---

## CI/CD Pipeline

The project uses GitHub Actions (`.github/workflows/build.yml`) to automatically compile and release executables. Push a new tag with the version matching `version.json` to trigger compilation:
```bash
git tag v2.0.3
git push origin v2.0.3
```
This compile check tests execution compatibility, runs PyInstaller tasks for macOS/Windows/Linux, and automatically attaches build artifacts directly to the tag release.
