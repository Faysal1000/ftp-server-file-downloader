# SAMOnline FTP Downloader

A desktop application for browsing and downloading files from HTTP open directory listings. It offers an easy-to-use graphical interface to automatically traverse server directory structures, allowing you to bulk-download folders or specific files while preserving the remote folder hierarchy.

**No coding knowledge required** — download a single file, double-click, and start downloading.

---

## Quick Start

Go to the [**Releases**](../../releases/latest) page and download the file for your operating system:

| File                                       | Platform                     |
| ------------------------------------------ | ---------------------------- |
| `FTP-Downloader-Windows.exe`               | Windows 10/11 (64-bit)       |
| `FTP-Downloader-macOS-AppleSilicon.zip`    | macOS (Apple M1/M2/M3/M4/M5) |
| `FTP-Downloader-Linux`                     | Ubuntu / Debian / Fedora     |

### Installation Instructions

**1. Windows**: Open Command Prompt (`cmd`) and paste this to automatically download it to your Desktop:
```cmd
cd "%USERPROFILE%\Desktop" & curl -L -O https://github.com/Faysal1000/ftp-server-file-downloader/releases/latest/download/FTP-Downloader-Windows.exe
```
*(Double-click to run. If Windows SmartScreen warns you, click "More info" → "Run anyway")*

**2. macOS (Apple Silicon)**: Open **Terminal** and paste the exact command below. This will download the app, extract it, and automatically bypass Gatekeeper's quarantine warning so you can just double-click to open it:
```bash
cd ~/Desktop && curl -L -O https://github.com/Faysal1000/ftp-server-file-downloader/releases/latest/download/FTP-Downloader-macOS-AppleSilicon.zip && unzip -o FTP-Downloader-macOS-AppleSilicon.zip && rm FTP-Downloader-macOS-AppleSilicon.zip && chmod -R +x ~/Desktop/FTP-Downloader.app && xattr -cr ~/Desktop/FTP-Downloader.app
```
*(Double click the `FTP-Downloader.app` on your Desktop to run)*

**3. Linux**: Open your terminal and paste this command to download it and make it executable:
```bash
cd ~/Desktop && curl -L -O https://github.com/Faysal1000/ftp-server-file-downloader/releases/latest/download/FTP-Downloader-Linux && chmod +x FTP-Downloader-Linux
```

---

## Core Features

- **Automated Directory Scraping**: Enter a target URL (e.g., `http://example.com/files/`) and the app will recursively scan all subdirectories to map out available files.
- **Selective Downloading**: Select specific files or entire folders to download using the checkboxes.
- **Hierarchy Preservation**: Downloads maintain the exact folder structure of the remote server.
- **Background Downloads & Resumes**: Pause, cancel, and resume active downloads. 
- **Auto-Updater**: The application has an integrated updater. It will automatically ping GitHub on startup and notify you when a new version is released.

---

## For Developers

```bash
# Clone the repository
git clone https://github.com/Faysal1000/ftp-server-file-downloader.git
cd ftp-server-file-downloader

# Install Python 3.12 dependencies
pip install -r requirements.txt

# Run the app locally
python main.py
```

### GitHub Actions CI/CD
The project includes a GitHub Actions workflow (`.github/workflows/build.yml`) that automatically builds executables for all platforms using PyInstaller. Push a version tag (e.g., `git tag v1.0.0 && git push origin v1.0.0`) to trigger a build and create a GitHub Release.
