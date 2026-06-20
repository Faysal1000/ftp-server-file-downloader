# SAMOnline FTP Downloader — Full Product Specification

> **Version**: 2.0  
> **Type**: Cross-platform Desktop Application (macOS / Windows / Linux)  
> **Tech Stack**: Python (Flask backend) + HTML/CSS/JS/can use react or whatever u prefer which is best and have more conmtrol.. even can use tyailwind css or react naticve or swft or whatever is best opf the best for this kind of single application (PyWebView frontend)  
> **Single-file deployment**: Bundled via PyInstaller into one executable.. it will not install to the program files.. it is just an app thats it.. one file when i run it will work all the python and necessary things is packed in that one file so any computer can run.

---

## 1. Application Layout

The app uses a **two-column layout** (NO right sidebar):

```
┌──────────────┬──────────────────────────────────────────────┐
│              │                                              │
│   LEFT       │              MAIN CONTENT AREA               │
│   SIDEBAR    │       (changes based on active nav)          │
│   (fixed)    │                                              │
│              │                                              │
│              │                                              │
│              │                                              │
│              │                                              │
│              │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

- **Left Sidebar**: Fixed width (~200px), always visible, dark background.
- **Main Content Area**: Flexible width, fills remaining space. Content swaps based on which navigation item is active.

---

## 2. Left Sidebar (Always Visible)

### 2.1 Logo / Branding
- App icon (cloud emoji or custom SVG)
- App name: **SAMOnline**
- Subtitle: **FTP Downloader**

### 2.2 Navigation Menu
Four navigation items, each with an icon. Clicking one changes the **Main Content Area**.

| Icon | Label        | Description                                |
|------|--------------|--------------------------------------------|
| 📥   | **Home**     | Default view. The downloader workspace.    |
| 📋   | **Downloads**| History of completed/failed downloads.     |
| ⚙️   | **Settings** | App configuration and preferences.         |
| ℹ️   | **About**    | App version, credits, links.               |

- The **active** nav item has a highlighted background (accent purple/green pill).
- Hover effect on inactive items (subtle glow).

### 2.3 Storage Widget
Displays disk usage of the **download destination folder**.

- **Storage ring** (circular SVG progress indicator):
  - Shows percentage of disk used.
  - Ring color: green when < 80%, yellow when 80-90%, red when > 90%.
- **Text below ring**:
  - `XX% Used`
  - `XX.XX GB / YY.YY GB`
- Updates in real-time during downloads.

### 2.4 Connection Status
Sits at the very bottom of the sidebar.

- **Green dot** + `Connected` — when the app has internet connectivity (`navigator.onLine` is `true`).
- **Red dot** + `Disconnected` — when the app loses internet (`navigator.onLine` is `false`).
- Additionally, when a server URL has been inspected, show:
  - `Server reachable` or `Server unreachable` below the connection label.

---

## 3. Main Content Area — HOME View (Default)

This is the primary workspace. It has the following sections from top to bottom:

### 3.1 URL Input Bar (Top)
A single horizontal bar at the very top of the content area.

```
┌─────────────────────────────────────────────────────────────────────┐
│  🌐  [ http://172.16.50.9/DHAKA-FLIX-9/...               ]  [Inspect Folder]  [Stop]  │
└─────────────────────────────────────────────────────────────────────┘
```

- **URL Input Field**: Full-width text input with a globe icon prefix.
  - Placeholder: `Paste URL here...`
  - Supports encoded URLs with special characters.
- **Inspect Folder** button (primary accent color):
  - Triggers the directory scan.
  - Disabled while a scan or download is already running.
- **Stop** button (secondary):
  - Stops the current scan.
  - Disabled when no scan is running.
- **Nothing else** in this bar. No save path, no checkboxes, no advanced options. Those live in Settings.

### 3.2 Progress / Logs Tabs
Two tabs directly below the URL bar.

| Tab          | What it shows                                      |
|--------------|---------------------------------------------------|
| **Progress** | Dashboard stats + File tree + Action bar (default) |
| **Logs**     | Full chronological activity log of the software    |

- Active tab has an underline accent indicator.
- Switching tabs swaps the content below.

---

### 3.3 Progress Tab Content

#### 3.3.1 Dashboard Stats Row
A single horizontal row of stat cards. All cards are equal width, arranged in a flex row.

| Card           | Value Example | Description                              |
|----------------|---------------|------------------------------------------|
| Total Files    | `82`          | Number of files found during scan        |
| Completed      | `19` (green)  | Files successfully downloaded            |
| Remaining      | `63` (blue)   | Files not yet downloaded                 |
| Total Size     | `25.73 GB`    | Sum of all file sizes                    |
| Speed          | `12.4 MB/s`   | Current download speed                   |
| ETA            | `22 mins`     | Estimated time remaining                 |
| Progress       | `23%` + bar   | Overall progress percentage with bar     |
| Elapsed Time   | `00:02:14`    | Time since download started              |

- Cards have dark background with subtle border.
- Values are large, bold, and color-coded.
- The progress card spans wider and includes a horizontal progress bar beneath the percentage.

#### 3.3.2 File Tree Table
The core of the application. A scrollable table showing the full directory structure.

**Table Columns:**

| Column     | Width | Description                                           |
|------------|-------|-------------------------------------------------------|
| ☐ (Select) | 40px  | Checkbox for selecting files/folders for download     |
| Name       | 45%   | File/folder name with indent + icon (📁 or 📄)        |
| Size       | 12%   | Human-readable file size (e.g., `391.42 MB`)          |
| Type       | 8%    | `Folder` or `File`                                    |
| Status     | 15%   | Current state (see status list below)                 |
| Progress   | 12%   | Inline mini progress bar (only during download)       |
| Speed      | 8%    | Per-file download speed (e.g., `3.4 MB/s` or `–`)    |

**File/Folder Behaviors:**

1. **Collapsible Folders**:
   - Click the folder row's expand/collapse arrow (`▶` / `▼`) to show/hide children.
   - Folders start **expanded** after scan.
   - Nested folders are indented (20px per depth level).

2. **Checkbox Selection**:
   - Each file has an individual checkbox.
   - Each folder has a checkbox that **selects/deselects ALL children** recursively.
   - A **partially selected** folder shows an indeterminate (`━`) state.
   - The header row has a "Select All" checkbox.

3. **Status Values**:

   | Status Icon | Label          | Color  | When                                    |
   |-------------|----------------|--------|-----------------------------------------|
   | `✓`         | Ready          | Gray   | After scan, before download             |
   | `⬇`         | Downloading    | Blue   | Currently being downloaded              |
   | `✓`         | Found          | Green  | Successfully downloaded                 |
   | `⚠`         | Error          | Red    | Download failed                         |
   | `⏭`         | Skipped        | Yellow | User clicked Skip on this file          |
   | `⏸`         | Paused         | Orange | Download paused                         |
   | `─`         | Queued         | Gray   | Waiting in download queue               |

4. **Per-File Skip Button**:
   - When a file is actively downloading (`Downloading` status), a small **Skip ⏭** button appears in its row.
   - Clicking it immediately stops downloading that file, marks it as `Skipped`, and moves to the next file.
   - The `.part` file is kept on disk (can be resumed later).

#### 3.3.3 Bottom Action Bar
A sticky bar at the bottom of the main content area.

```
┌──────────────────────────────────────────────────────────────────────┐
│  [⬇ Download Selected]  [Download All]  │  Status text  │  [Clear Selection]  [⏸ Pause]  [⊗ Cancel]  │
└──────────────────────────────────────────────────────────────────────┘
```

| Button              | Description                                                  |
|---------------------|--------------------------------------------------------------|
| **Download Selected** | Downloads only the checked files/folders. Primary button.  |
| **Download All**    | Downloads everything found in the scan. Secondary button.    |
| **Clear Selection** | Unchecks all checkboxes in the file tree.                    |
| **Pause**           | Pauses the current download (keeps `.part` files).           |
| **Cancel**          | Cancels all downloads, clears queue. Asks for confirmation.  |

- **Status text** in the middle shows current activity:
  - `Idle` — nothing happening.
  - `Scanning: http://...` — during inspection.
  - `Downloading: [MsV] Ben 10 Omniverse S01E01...` — shows active file name.
  - `Paused` — when paused.
  - `Complete! 82 files downloaded.` — when finished.

---

### 3.4 Logs Tab Content

When the **Logs** tab is active, the entire content area below the tabs is replaced with a full-height scrollable log viewer.

**Log Entry Format:**
```
[HH:MM:SS]  [TYPE]  Message
```

**Log Types:**

| Type     | Color  | Example                                                      |
|----------|--------|--------------------------------------------------------------|
| `INFO`   | White  | `Inspection started for http://172.16.50.9/...`              |
| `SCAN`   | Cyan   | `Found folder: Season 1/`                                    |
| `SCAN`   | Cyan   | `Found file: [MsV] Ben 10 S01E01.mkv (391.42 MB)`           |
| `DOWN`   | Green  | `Downloaded: [MsV] Ben 10 S01E01.mkv (391.42 MB)`           |
| `SKIP`   | Yellow | `Skipped: [MsV] Ben 10 S01E03.mkv (user requested)`         |
| `ERROR`  | Red    | `Failed: [MsV] Ben 10 S01E05.mkv — 404 Not Found`           |
| `WARN`   | Orange | `Slow connection detected. Speed: 0.2 MB/s`                 |
| `SYSTEM` | Purple | `Download complete. 82 files, 25.73 GB in 00:35:12`         |

**Features:**
- Auto-scrolls to bottom as new entries arrive.
- **Clear Log** button in top-right corner.
- **Copy All** button to copy full log to clipboard.
- **Export Log** button to save log as `.txt` file.
- Logs persist across tab switches (they are not cleared when switching to Progress).
- All events across the entire application lifecycle are logged here.

---

## 4. Main Content Area — DOWNLOADS View

Shows a history of all past download sessions.

### 4.1 Download History Table

| Column       | Description                                   |
|--------------|-----------------------------------------------|
| Date         | When the download session started              |
| Source URL   | The directory URL that was inspected           |
| Files        | Total files downloaded / total found           |
| Total Size   | Total data downloaded                          |
| Duration     | How long the download took                     |
| Status       | `Complete`, `Partial`, `Cancelled`, `Error`    |
| Actions      | `Re-download`, `Open Folder`, `Delete Record`  |

### 4.2 Features
- Sortable columns (click header to sort).
- Search/filter bar at the top.
- Pagination or infinite scroll for large history.
- `Clear History` button.

---

## 5. Main Content Area — SETTINGS View

When **Settings** is clicked in the sidebar, the main content area shows all app configuration options. Organized into sections with clear headings.

### 5.1 Download Settings

| Setting                    | Type       | Default                              | Description                                           |
|---------------------------|------------|--------------------------------------|-------------------------------------------------------|
| **Download Folder**        | Path input | `~/Downloads/SAMOnline FTP Downloads` | Default save location. Has a `Browse` button.         |
| **Overwrite Existing Files** | Toggle  | `OFF`                                | If ON, re-downloads overwrite existing files.         |
| **Resume Broken Downloads** | Toggle   | `ON`                                 | If ON, resumes `.part` files from where they stopped. |
| **Skip Completed Files**   | Toggle    | `ON`                                 | If ON, skips files that already exist with correct size. |
| **Auto-close on Finish**   | Toggle    | `OFF`                                | If ON, app closes automatically when all downloads complete. |
| **Preserve Folder Structure** | Toggle | `ON`                                 | If ON, recreates server's folder hierarchy locally.   |

### 5.2 Network Settings

| Setting                      | Type         | Default | Description                                          |
|------------------------------|--------------|---------|------------------------------------------------------|
| **Max Concurrent Downloads** | Number input | `1`     | How many files to download simultaneously (1–10).    |
| **Connection Timeout**       | Number input | `30`    | Seconds before a connection attempt is abandoned.     |
| **Download Chunk Size**      | Dropdown     | `8 MB`  | Size of each download chunk (1 MB, 4 MB, 8 MB, 16 MB). |
| **Retry Failed Downloads**   | Toggle       | `ON`    | If ON, retries failed downloads up to N times.        |
| **Max Retries**              | Number input | `3`     | Number of retry attempts for failed downloads.        |
| **User Agent**               | Text input   | `Mozilla/5.0 ...` | Custom user agent string for requests.       |
| **Rate Limit**               | Number input | `0`     | Max download speed in MB/s. `0` = unlimited.          |

### 5.3 Scan Settings

| Setting                    | Type   | Default | Description                                             |
|---------------------------|--------|---------|---------------------------------------------------------|
| **Ask Server for File Sizes** | Toggle | `ON`  | Sends HEAD requests to get accurate file sizes.         |
| **Max Scan Depth**         | Number | `10`    | Maximum folder nesting depth to scan.                   |
| **File Type Filter**       | Text   | `*`     | Comma-separated extensions to include (e.g., `mkv,mp4`). `*` = all. |
| **Exclude Pattern**        | Text   | (empty) | Glob pattern for files/folders to exclude (e.g., `*.txt,thumbs/`). |

### 5.4 Notification Settings

| Setting                      | Type   | Default | Description                                        |
|-----------------------------|--------|---------|----------------------------------------------------|
| **System Notification on Complete** | Toggle | `ON` | macOS/Windows notification when downloads finish. |
| **Sound Alert on Complete**  | Toggle | `OFF`   | Play a sound when all downloads are done.          |
| **Notification on Error**    | Toggle | `ON`    | Notify when a download fails.                      |

### 5.5 Appearance Settings

| Setting            | Type     | Default  | Description                              |
|-------------------|----------|----------|------------------------------------------|
| **Theme**          | Dropdown | `Dark`   | `Dark`, `Light`, `System`.               |
| **Accent Color**   | Color    | `#6c5ce7` | Primary accent color for buttons/UI.    |
| **Font Size**      | Dropdown | `Medium` | `Small`, `Medium`, `Large`.              |

### 5.6 Actions

| Button             | Description                                        |
|--------------------|----------------------------------------------------|
| **Save Settings**  | Persists all changes to a local config file.       |
| **Reset Defaults** | Reverts all settings to their default values.      |
| **Open Config File** | Opens the JSON config file in the system editor. |

- Settings are saved to `~/.samonline/config.json`.
- Settings load on app startup.

---

## 6. Main Content Area — ABOUT View

### 6.1 Content
- **App Name**: SAMOnline FTP Downloader
- **Version**: `2.0.0`
- **Description**: A premium desktop application for browsing and downloading files from HTTP open directory listings.
- **Developer**: Faysal Ahmmed
- **License**: Personal Use
- **Links**: GitHub repository (if applicable)
- **System Info**: OS, Python version, disk space

### 6.2 Features
- **Check for Updates** button (optional, for future use).
- **Report Bug** link.

---

## 7. Interaction Flows

### 7.1 Full Scan & Download Flow

```
1. User opens app → HOME view is shown with empty state.
2. User pastes URL into the URL input bar.
3. User clicks "Inspect Folder".
4. URL bar shows a loading spinner. Stop button becomes active.
5. The file tree populates in real-time as folders/files are discovered.
6. Dashboard stats update live (Total Files, Total Size counters increment).
7. Logs tab records every folder/file found.
8. When scan completes:
   a. All checkboxes are checked by default.
   b. "Download Selected" and "Download All" buttons become active.
   c. Status text: "Scan complete. Found 82 files (25.73 GB) in 9 folders."
9. User optionally unchecks files they don't want.
10. User clicks "Download Selected" or "Download All".
11. Downloads begin sequentially (or concurrently per settings).
12. Each file row shows:
    - Status changes: Queued → Downloading → Found/Error/Skipped
    - Inline progress bar fills up
    - Speed column shows per-file speed
    - Skip button appears on the active download
13. Dashboard updates in real-time:
    - Completed count increments
    - Remaining count decrements
    - Progress bar advances
    - Speed and ETA update
    - Elapsed time ticks
14. Storage widget on sidebar updates as files land on disk.
15. When complete:
    - Status: "Complete! 82 files downloaded in 00:35:12"
    - System notification (if enabled in settings)
    - Auto-close (if enabled in settings)
```

### 7.2 Selective Download Flow

```
1. After scan, user unchecks "Select All".
2. User expands "Season 1" folder, checks only episodes 1-5.
3. User clicks "Download Selected".
4. Only checked files are queued for download.
5. Unchecked files remain in "Ready" status.
```

### 7.3 Skip File Flow

```
1. File X is currently downloading at 46%.
2. User clicks the "Skip ⏭" button on that row.
3. Download immediately stops for File X.
4. File X status changes to "Skipped" (yellow).
5. The .part file remains on disk.
6. Download moves to the next queued file.
```

### 7.4 Pause & Resume Flow

```
1. Download is in progress.
2. User clicks "Pause".
3. All active downloads halt, .part files are kept.
4. Button changes to "Resume".
5. User clicks "Resume".
6. Downloads continue from where they stopped.
```

---

## 8. Data Structures

### 8.1 Scanned File Object
```json
{
  "url": "http://172.16.50.9/..../file.mkv",
  "rel_path": "Season 1/file.mkv",
  "size": 391420000,
  "type": "file",
  "status": "ready",
  "progress": 0,
  "speed": 0,
  "selected": true
}
```

### 8.2 Folder Object
```json
{
  "path": "Season 1/",
  "type": "folder",
  "expanded": true,
  "selected": true,
  "children": []
}
```

### 8.3 Config Object (`~/.samonline/config.json`)
```json
{
  "download_folder": "~/Downloads/SAMOnline FTP Downloads",
  "overwrite_files": false,
  "resume_broken": true,
  "skip_completed": true,
  "auto_close": false,
  "preserve_structure": true,
  "max_concurrent": 1,
  "timeout": 30,
  "chunk_size": 8388608,
  "retry_failed": true,
  "max_retries": 3,
  "user_agent": "Mozilla/5.0 ...",
  "rate_limit": 0,
  "ask_sizes": true,
  "max_depth": 10,
  "file_filter": "*",
  "exclude_pattern": "",
  "notify_complete": true,
  "sound_alert": false,
  "notify_error": true,
  "theme": "dark",
  "accent_color": "#6c5ce7",
  "font_size": "medium"
}
```

---

## 9. Empty States & Edge Cases

| Scenario                          | What to show                                                  |
|----------------------------------|---------------------------------------------------------------|
| App first opened                 | Empty file tree with ghost text: "Paste a URL and click Inspect to start" |
| Scan finds 0 files              | Message: "No downloadable files found at this URL."           |
| URL is invalid                  | Inline error under URL input: "Invalid URL format."           |
| Server is unreachable           | Error toast + log entry: "Could not connect to server."       |
| Internet disconnected mid-download | Pause automatically, show warning, retry when back online.  |
| Disk full during download       | Stop download, show error toast, log entry.                   |
| Duplicate URL scan              | Ask: "You already scanned this URL. Clear results and rescan?" |
| Very large directory (1000+ files) | Show loading indicator, lazy-load tree nodes.              |

---

## 10. Keyboard Shortcuts

| Shortcut       | Action                    |
|----------------|---------------------------|
| `Ctrl/Cmd + V` | Paste URL into input      |
| `Ctrl/Cmd + A` | Select all files          |
| `Ctrl/Cmd + D` | Start download            |
| `Escape`       | Stop scan / Cancel dialog |
| `Space`        | Pause / Resume download   |
| `Ctrl/Cmd + L` | Switch to Logs tab        |
| `Ctrl/Cmd + ,` | Open Settings             |

---

## 11. File Structure

```
Downloader/
├── agent.md              ← This specification file
├── app.py                ← Core scanning/parsing logic (DirectoryScanner, RemoteFile)
├── main.py               ← Entry point (launches Flask + PyWebView)
├── backend/
│   └── server.py         ← Flask API routes & SSE event stream
└── frontend/
    ├── index.html         ← App shell & layout
    ├── style.css          ← All styles (dark theme, animations)
    └── script.js          ← Frontend logic (API calls, tree rendering, state)
```

---

## 12. Design Principles

1. **Dark Theme First**: Deep navy/charcoal backgrounds (`#0f111a`, `#151828`, `#1a1d2d`).
2. **Accent Colors**: Neon green for success (`#00d26a`), purple for primary actions (`#6c5ce7`), red for danger (`#ff6b6b`).
3. **Glassmorphism**: Subtle transparency and blur on cards and sidebar.
4. **Micro-animations**: Button hover glows, progress bar shimmer, status dot pulse, smooth expand/collapse.
5. **Typography**: Inter font, clean weights (400, 500, 600, 700).
6. **Spacing**: Consistent 8px grid system.
7. **No clutter**: Every pixel earns its place. If it's not essential, it's in Settings.
