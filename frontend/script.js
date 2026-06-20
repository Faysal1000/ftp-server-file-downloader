const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const els = {
    urlInput: $("#url-input"),
    urlError: $("#url-error"),
    inspectBtn: $("#inspect-btn"),
    stopScanBtn: $("#stop-scan-btn"),
    clearInspectBtn: $("#clear-inspect-btn"),
    downloadSelectedBtn: $("#download-selected-btn"),
    downloadAllBtn: $("#download-all-btn"),
    clearSelectionBtn: $("#clear-selection-btn"),
    pauseBtn: $("#pause-btn"),
    cancelBtn: $("#cancel-btn"),
    fileBody: $("#file-body"),
    emptyState: $("#empty-state"),
    selectAll: $("#select-all"),
    activityText: $("#activity-text"),
    logViewer: $("#log-viewer"),
    clearLogBtn: $("#clear-log-btn"),
    copyLogBtn: $("#copy-log-btn"),
    exportLogBtn: $("#export-log-btn"),
    toastRoot: $("#toast-root"),
    networkDot: $("#network-dot"),
    networkLabel: $("#network-label"),
    serverLabel: $("#server-label"),
    storageRing: $("#storage-ring"),
    storagePercent: $("#storage-percent"),
    storageUsed: $("#storage-used"),
    storageFolder: $("#storage-folder"),
    historyBody: $("#history-body"),
    historyEmpty: $("#history-empty"),
    historySearch: $("#history-search"),
    clearHistoryBtn: $("#clear-history-btn"),
    refreshHistoryBtn: $("#refresh-history-btn"),
    saveSettingsBtn: $("#save-settings-btn"),
    resetSettingsBtn: $("#reset-settings-btn"),
    browseFolderBtn: $("#browse-folder-btn"),
    openFolderBtn: $("#open-folder-btn"),
    systemList: $("#system-list"),
    aboutVersion: $("#about-version"),
    paletteGrid: $("#palette-grid"),
    appearanceSummary: $("#appearance-summary"),
};

const settingEls = {
    download_folder: $("#setting-download-folder"),
    overwrite_files: $("#setting-overwrite"),
    resume_broken: $("#setting-resume"),
    skip_completed: $("#setting-skip-completed"),
    auto_close: $("#setting-auto-close"),
    preserve_structure: $("#setting-preserve"),
    max_concurrent: $("#setting-concurrent"),
    timeout: $("#setting-timeout"),
    chunk_size: $("#setting-chunk-size"),
    retry_failed: $("#setting-retry-failed"),
    max_retries: $("#setting-max-retries"),
    user_agent: $("#setting-user-agent"),
    rate_limit: $("#setting-rate-limit"),
    ask_sizes: $("#setting-ask-sizes"),
    max_depth: $("#setting-max-depth"),
    file_filter: $("#setting-file-filter"),
    exclude_pattern: $("#setting-exclude"),
    notify_complete: $("#setting-notify-complete"),
    sound_alert: $("#setting-sound"),
    notify_error: $("#setting-notify-error"),
    theme: $("#setting-theme"),
    appearance_preset: $("#setting-appearance-preset"),
    font_size: $("#setting-font-size"),
};

const statsEls = {
    totalFiles: $("#stat-total-files"),
    completed: $("#stat-completed"),
    skipped: $("#stat-skipped"),
    remaining: $("#stat-remaining"),
    selected: $("#stat-selected"),
    totalSize: $("#stat-total-size"),
    speed: $("#stat-speed"),
    eta: $("#stat-eta"),
    progress: $("#stat-progress"),
    progressBar: $("#overall-progress"),
    elapsed: $("#stat-elapsed"),
};

const state = {
    config: {},
    nodes: new Map(),
    files: new Map(),
    roots: [],
    logs: [],
    history: [],
    historySort: { key: "date", dir: "desc" },
    currentView: "home",
    currentTab: "progress",
    scannedUrl: "",
    isScanning: false,
    isDownloading: false,
    isPaused: false,
    downloadStartedAt: null,
    completedCount: 0,
    skippedCount: 0,
    failedCount: 0,
    serverReachable: null,
};

const statusMeta = {
    ready: ["✓", "Ready"],
    queued: ["─", "Queued"],
    downloading: ["⬇", "Downloading"],
    complete: ["✓", "Found"],
    error: ["⚠", "Error"],
    skipped: ["⏭", "Skipped"],
    paused: ["⏸", "Paused"],
    cancelled: ["⊗", "Cancelled"],
};

const palettes = {
    violet: { name: "Violet Stream", accent: "#6c5ce7", accent2: "#9b8cff", bg: "#0f111a", panel: "#151828", panel2: "#1a1d2d", line: "#2b3047" },
    emerald: { name: "Emerald Pulse", accent: "#00b894", accent2: "#42e6a4", bg: "#081713", panel: "#10231f", panel2: "#142b26", line: "#214239" },
    cyan: { name: "Cyan Circuit", accent: "#00bcd4", accent2: "#56e5f6", bg: "#07151c", panel: "#0f222b", panel2: "#142c36", line: "#21424d" },
    amber: { name: "Amber Drive", accent: "#f59e0b", accent2: "#ffd166", bg: "#16110a", panel: "#211a10", panel2: "#2b2113", line: "#46351d" },
    rose: { name: "Rose Signal", accent: "#f43f5e", accent2: "#fb7185", bg: "#160b12", panel: "#24121b", panel2: "#301725", line: "#4c2435" },
    blue: { name: "Blue Relay", accent: "#3b82f6", accent2: "#7db3ff", bg: "#09111f", panel: "#111c30", panel2: "#17243a", line: "#283b5a" },
    lime: { name: "Lime Neon", accent: "#84cc16", accent2: "#bef264", bg: "#101507", panel: "#1a220e", panel2: "#222d13", line: "#3a4a20" },
    coral: { name: "Coral Sync", accent: "#ff6b6b", accent2: "#ffa08e", bg: "#170e0f", panel: "#261617", panel2: "#321d1e", line: "#4d2b2d" },
    graphite: { name: "Graphite Gold", accent: "#d4af37", accent2: "#f2d675", bg: "#0f1012", panel: "#191b1f", panel2: "#20242a", line: "#343944" },
    indigo: { name: "Indigo Night", accent: "#4f46e5", accent2: "#818cf8", bg: "#0c1020", panel: "#131a31", panel2: "#19213c", line: "#293455" },
};

function formatBytes(bytes, decimals = 2) {
    if (!Number.isFinite(Number(bytes)) || Number(bytes) <= 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB", "PB"];
    let value = Number(bytes);
    let index = 0;
    while (value >= 1024 && index < units.length - 1) {
        value /= 1024;
        index += 1;
    }
    return `${value.toFixed(index === 0 ? 0 : decimals)} ${units[index]}`;
}

function formatDuration(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) return "--";
    seconds = Math.floor(seconds);
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return [h, m, s].map((part) => String(part).padStart(2, "0")).join(":");
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
    const init = {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
    };
    const response = await fetch(path, init);
    const text = await response.text();
    const payload = text ? JSON.parse(text) : {};
    if (!response.ok) {
        throw new Error(payload.error || `Request failed: ${response.status}`);
    }
    return payload;
}

function toast(message, kind = "info") {
    const item = document.createElement("div");
    item.className = `toast ${kind}`;
    item.textContent = message;
    els.toastRoot.appendChild(item);
    setTimeout(() => item.remove(), 3600);

    if (kind === "error") {
        playSoundAlert("error");
    }
}

function playSoundAlert(soundType) {
    if (!state.config?.sound_alert) return;
    if (window.pywebview?.api?.play_sound) {
        window.pywebview.api.play_sound(soundType);
    } else {
        try {
            const filename = soundType === "success" ? "notification.mp3" : "error.mp3";
            const audio = new Audio(`assets/${filename}`);
            audio.play().catch((err) => console.warn(`Failed to play ${soundType} notification sound:`, err));
        } catch (e) {
            console.warn("Audio playback exception:", e);
        }
    }
}

function updateActivityTextSelection() {
    const selectedCount = getSelectedFileIds().length;
    if (selectedCount > 0) {
        const files = Array.from(state.files.values()).filter((f) => f.selected);
        const totalSize = files.reduce((sum, file) => sum + Number(file.size || 0), 0);
        els.activityText.textContent = `${selectedCount} file${selectedCount === 1 ? "" : "s"} selected for download (${formatBytes(totalSize)})`;
    } else if (state.files.size > 0) {
        els.activityText.textContent = `No files selected (Total: ${state.files.size} file${state.files.size === 1 ? "" : "s"})`;
    } else {
        els.activityText.textContent = "Idle";
    }
}

function setBusyControls() {
    els.inspectBtn.disabled = state.isScanning || state.isDownloading;
    els.stopScanBtn.disabled = !state.isScanning;
    els.clearInspectBtn.disabled = state.isScanning || state.isDownloading;
    const hasFiles = state.files.size > 0;
    const selectedCount = getSelectedFileIds().length;
    els.downloadSelectedBtn.disabled = state.isScanning || state.isDownloading || selectedCount === 0;
    els.downloadSelectedBtn.textContent = `⬇ Download Selected (${selectedCount})`;
    els.downloadAllBtn.disabled = state.isScanning || state.isDownloading || !hasFiles;
    els.clearSelectionBtn.disabled = !hasFiles || state.isScanning || state.isDownloading;
    els.pauseBtn.disabled = !state.isDownloading;
    els.pauseBtn.textContent = state.isPaused ? "▶ Resume" : "⏸ Pause";
    els.cancelBtn.disabled = !state.isDownloading;
}

function hexToRgb(hex) {
    const clean = String(hex || "").replace("#", "");
    if (!/^[0-9a-f]{6}$/i.test(clean)) return { r: 108, g: 92, b: 231 };
    return {
        r: parseInt(clean.slice(0, 2), 16),
        g: parseInt(clean.slice(2, 4), 16),
        b: parseInt(clean.slice(4, 6), 16),
    };
}

function mixHex(hex, percent) {
    const { r, g, b } = hexToRgb(hex);
    const target = percent >= 0 ? 255 : 0;
    const amount = Math.abs(percent);
    const mix = (channel) => Math.round(channel + (target - channel) * amount);
    return `#${[mix(r), mix(g), mix(b)].map((value) => value.toString(16).padStart(2, "0")).join("")}`;
}

function applyCssVar(name, value) {
    document.documentElement.style.setProperty(name, value);
}

function currentPalette() {
    return palettes[state.config.appearance_preset] || palettes.violet;
}

function applyAppearance() {
    const config = state.config || {};
    const systemLight = window.matchMedia?.("(prefers-color-scheme: light)").matches;
    const light = config.theme === "light" || (config.theme === "system" && systemLight);
    const palette = currentPalette();
    const accent = config.accent_color || palette.accent;
    const accent2 = mixHex(accent, 0.28);
    const { r, g, b } = hexToRgb(accent);

    document.body.classList.toggle("theme-light", light);
    document.body.classList.toggle("font-small", config.font_size === "small");
    document.body.classList.toggle("font-large", config.font_size === "large");

    applyCssVar("--accent", accent);
    applyCssVar("--accent-2", accent2);
    applyCssVar("--accent-rgb", `${r}, ${g}, ${b}`);
    applyCssVar("--accent-soft", `rgba(${r}, ${g}, ${b}, 0.14)`);
    applyCssVar("--accent-strong", `rgba(${r}, ${g}, ${b}, 0.24)`);
    applyCssVar("--accent-border", `rgba(${r}, ${g}, ${b}, 0.46)`);
    applyCssVar("--accent-shadow", `rgba(${r}, ${g}, ${b}, 0.24)`);


    applyCssVar("--focus-ring", `rgba(${r}, ${g}, ${b}, 0.16)`);
    applyCssVar("--purple", accent);
    applyCssVar("--purple-2", accent2);

    if (light) {
        applyCssVar("--bg", "#f4f6fb");
        applyCssVar("--panel", "#ffffff");
        applyCssVar("--panel-2", "#f7f9ff");
        applyCssVar("--panel-3", "#edf1fb");
        applyCssVar("--line", "#dce2ef");
        applyCssVar("--line-soft", "rgba(18, 26, 43, 0.1)");
        applyCssVar("--text", "#151a29");
        applyCssVar("--muted", "#607089");
        applyCssVar("--dim", "#8a96a9");
        applyCssVar("--input-bg", "#ffffff");
    } else {
        applyCssVar("--bg", palette.bg);
        applyCssVar("--panel", palette.panel);
        applyCssVar("--panel-2", palette.panel2);
        applyCssVar("--panel-3", mixHex(palette.panel2, 0.06));
        applyCssVar("--line", palette.line);
        applyCssVar("--line-soft", "rgba(255, 255, 255, 0.08)");
        applyCssVar("--text", "#f4f6fb");
        applyCssVar("--muted", "#9aa3b8");
        applyCssVar("--dim", "#687188");
        applyCssVar("--input-bg", "#111421");

        // Dynamically compute dark surfaces based on selected preset
        const panelRgb = hexToRgb(palette.panel);
        const bgRgb = hexToRgb(palette.bg);
        applyCssVar("--surface-1", `rgba(${panelRgb.r}, ${panelRgb.g}, ${panelRgb.b}, 0.82)`);
        applyCssVar("--surface-2", `rgba(${bgRgb.r}, ${bgRgb.g}, ${bgRgb.b}, 0.74)`);
        applyCssVar("--surface-3", `rgba(${bgRgb.r}, ${bgRgb.g}, ${bgRgb.b}, 0.92)`);
        applyCssVar("--surface-4", `rgba(${bgRgb.r}, ${bgRgb.g}, ${bgRgb.b}, 0.96)`);
        applyCssVar("--surface-5", `rgba(${panelRgb.r}, ${panelRgb.g}, ${panelRgb.b}, 0.5)`);
        applyCssVar("--surface-6", `rgba(${panelRgb.r}, ${panelRgb.g}, ${panelRgb.b}, 0.6)`);
        applyCssVar("--surface-7", `rgba(${panelRgb.r}, ${panelRgb.g}, ${panelRgb.b}, 0.78)`);
        applyCssVar("--surface-8", `rgba(${panelRgb.r}, ${panelRgb.g}, ${panelRgb.b}, 0.8)`);
        applyCssVar("--surface-solid", palette.panel);
        applyCssVar("--log-bg", palette.bg);
        applyCssVar("--track-bg", palette.panel2);
    }

    if (els.appearanceSummary) {
        els.appearanceSummary.textContent = palette.name;
    }
    syncChoiceButtons();
}

function applyConfigToForm(config) {
    Object.entries(settingEls).forEach(([key, el]) => {
        if (!el) return;
        if (el.type === "checkbox") {
            el.checked = Boolean(config[key]);
        } else {
            el.value = config[key] ?? "";
        }
    });
    syncChoiceButtons();
}

function syncChoiceButtons() {
    $$("[data-choice-for]").forEach((group) => {
        const key = group.dataset.choiceFor;
        const value = state.config[key] ?? settingEls[key]?.value;
        group.querySelectorAll("button[data-value]").forEach((button) => {
            button.classList.toggle("active", button.dataset.value === String(value));
        });
    });
    $$("#palette-grid .palette-option").forEach((button) => {
        button.classList.toggle("active", button.dataset.palette === state.config.appearance_preset);
    });
}

function renderPaletteGrid() {
    if (!els.paletteGrid) return;
    els.paletteGrid.innerHTML = Object.entries(palettes).map(([key, palette]) => `
        <button class="palette-option" type="button" data-palette="${key}" title="${escapeHtml(palette.name)}">
            <span class="palette-swatch" style="--swatch-a:${palette.accent};--swatch-b:${palette.accent2};--swatch-bg:${palette.panel2}"></span>
            <span>${escapeHtml(palette.name)}</span>
        </button>
    `).join("");
}

function updateConfigPreview(key, value) {
    state.config = { ...state.config, [key]: value };
    if (settingEls[key]) {
        if (settingEls[key].type === "checkbox") {
            settingEls[key].checked = Boolean(value);
        } else {
            settingEls[key].value = value;
        }
    }
    applyAppearance();
}

function readConfigFromForm() {
    const config = {};
    Object.entries(settingEls).forEach(([key, el]) => {
        if (!el) return;
        if (el.type === "checkbox") {
            config[key] = el.checked;
        } else if (el.type === "number") {
            config[key] = Number(el.value);
        } else if (key === "chunk_size") {
            config[key] = Number(el.value);
        } else {
            config[key] = el.value;
        }
    });
    config.accent_color = state.config.accent_color || currentPalette().accent;
    return config;
}

async function loadConfig() {
    const payload = await api("/api/config");
    state.config = payload.config;
    applyConfigToForm(state.config);
    applyAppearance();
    updateStorage();
}

async function saveSettings() {
    const config = readConfigFromForm();
    const payload = await api("/api/config", {
        method: "POST",
        body: JSON.stringify(config),
    });
    state.config = payload.config;
    applyConfigToForm(state.config);
    applyAppearance();
    updateStorage();
    toast("Settings saved", "success");
}

function resetTree() {
    state.nodes.clear();
    state.files.clear();
    state.roots = [];
    state.completedCount = 0;
    state.skippedCount = 0;
    state.failedCount = 0;
    renderTree();
    updateStats();
}

function folderId(path) {
    return `folder:${path || "root"}`;
}

function parentPath(path) {
    const clean = String(path || "").replace(/^\/+|\/+$/g, "");
    if (!clean.includes("/")) return "";
    return clean.split("/").slice(0, -1).join("/");
}

function baseName(path) {
    const clean = String(path || "").replace(/^\/+|\/+$/g, "");
    if (!clean) return "Root Directory";
    return clean.split("/").pop();
}

function ensureFolder(path) {
    const clean = String(path || "").replace(/^\/+|\/+$/g, "");
    const id = folderId(clean);
    if (state.nodes.has(id)) return state.nodes.get(id);
    const parent = clean ? ensureFolder(parentPath(clean)) : null;
    const node = {
        id,
        type: "folder",
        path: clean,
        name: clean ? baseName(clean) : "Root Directory",
        children: [],
        expanded: !clean,
        selected: true,
        partial: false,
        status: "ready",
        progress: 0,
        speed: 0,
    };
    state.nodes.set(id, node);
    if (parent) {
        if (!parent.children.includes(id)) parent.children.push(id);
    } else if (!state.roots.includes(id)) {
        state.roots.push(id);
    }
    return node;
}

function addFolder(path) {
    ensureFolder(path);
    renderTree();
}

function addFile(file) {
    const parent = ensureFolder(parentPath(file.rel_path));
    const node = {
        ...file,
        type: "file",
        name: baseName(file.rel_path),
        selected: file.selected !== false,
        status: file.status || "ready",
        progress: Number(file.progress || 0),
        speed: Number(file.speed || 0),
        downloaded: Number(file.downloaded || 0),
    };
    state.files.set(node.id, node);
    state.nodes.set(node.id, node);
    if (!parent.children.includes(node.id)) parent.children.push(node.id);
    refreshFolderSelection();
    renderTree();
    updateStats();
}

function updateFile(file) {
    const existing = state.files.get(file.id);
    if (!existing) {
        addFile(file);
        return;
    }
    Object.assign(existing, file);
    state.nodes.set(file.id, existing);
    refreshFolderSelection();
    renderTree();
    updateStats();
}

function visibleRows() {
    const rows = [];
    const visit = (id, depth) => {
        const node = state.nodes.get(id);
        if (!node) return;
        rows.push({ node, depth });
        if (node.type === "folder" && node.expanded) {
            node.children.forEach((childId) => visit(childId, depth + 1));
        }
    };
    state.roots.forEach((id) => visit(id, 0));
    return rows;
}

function statusBadge(status) {
    const [icon, label] = statusMeta[status] || statusMeta.ready;
    return `<span class="status-badge status-${status}"><span>${icon}</span>${label}</span>`;
}

function renderTree() {
    const rows = visibleRows();
    els.fileBody.innerHTML = rows.map(({ node, depth }) => renderRow(node, depth)).join("");
    els.emptyState.classList.toggle("hidden", state.files.size > 0 || state.isScanning);
    els.fileBody.querySelectorAll("input[data-node-id]").forEach((input) => {
        const node = state.nodes.get(input.dataset.nodeId);
        input.checked = Boolean(node?.selected);
        input.indeterminate = Boolean(node?.partial);
    });
    updateSelectAllCheckbox();
    updateStats();
}

function renderRow(node, depth) {
    const indent = depth * 20;
    const isFolder = node.type === "folder";
    const icon = isFolder ? "📁" : `<img src="assets/file_icon.png" class="file-icon" alt="File">`;
    const expander = isFolder
        ? `<button class="expander" data-action="toggle-folder" data-id="${node.id}" aria-label="Toggle folder">${node.expanded ? "▼" : "▶"}</button>`
        : `<span class="expander"></span>`;
    const progressVal = Math.round(node.progress || 0);
    const progress = isFolder ? "" : `<div style="display:flex; align-items:center; gap:6px; width:100%;"><div class="mini-track" style="flex:1;"><div class="mini-fill" style="width:${Math.max(0, Math.min(100, node.progress || 0))}%"></div></div><span class="progress-text">${progressVal}%</span></div>`;
    const speed = isFolder ? "–" : (node.speed ? `${formatBytes(node.speed)}/s` : "–");
    const size = isFolder ? "–" : (node.size ? formatBytes(node.size) : "Unknown");
    const skip = node.status === "downloading"
        ? `<button class="btn secondary skip-row-btn" data-action="skip-file" data-id="${node.id}">Skip ⏭</button>`
        : "";
    return `
        <tr data-id="${node.id}">
            <td class="select-col"><input type="checkbox" data-node-id="${node.id}" aria-label="Select ${escapeHtml(node.name)}"></td>
            <td>
                <div class="file-name-cell" style="padding-left:${indent}px">
                    ${expander}
                    <span aria-hidden="true">${icon}</span>
                    <span class="row-name ${node.expandedName ? "expanded" : ""}" title="${escapeHtml(isFolder ? node.path || node.name : node.rel_path)}">${escapeHtml(node.name)}</span>
                </div>
            </td>
            <td class="size-cell">${size}</td>
            <td>${isFolder ? "Folder" : "File"}</td>
            <td>${statusBadge(node.status || "ready")}</td>
            <td><div class="row-actions">${progress}${skip}</div></td>
            <td class="speed-cell">${speed}</td>
        </tr>
    `;
}

function childFileIds(node) {
    if (!node || node.type === "file") return node ? [node.id] : [];
    return node.children.flatMap((id) => childFileIds(state.nodes.get(id)));
}

function setNodeSelection(id, selected) {
    const node = state.nodes.get(id);
    if (!node) return;
    node.selected = selected;
    node.partial = false;
    if (node.type === "folder") {
        node.children.forEach((childId) => setNodeSelection(childId, selected));
    }
}

function refreshFolderSelection() {
    const visit = (node) => {
        if (!node || node.type === "file") return Boolean(node?.selected);
        let selectedCount = 0;
        let partialCount = 0;
        let total = 0;
        let childStatuses = [];
        node.children.forEach((childId) => {
            const child = state.nodes.get(childId);
            if (!child) return;
            total += 1;
            if (child.type === "folder") {
                visit(child);
            }
            if (child.selected) selectedCount += 1;
            if (child.partial) partialCount += 1;
            if (child.status) childStatuses.push(child.status);
        });
        if (total > 0) {
            node.selected = selectedCount === total && partialCount === 0;
            node.partial = partialCount > 0 || (selectedCount > 0 && selectedCount < total);
            
            if (childStatuses.includes("downloading")) {
                node.status = "downloading";
            } else if (childStatuses.includes("paused")) {
                node.status = "paused";
            } else if (childStatuses.includes("queued")) {
                node.status = "queued";
            } else if (childStatuses.includes("error")) {
                node.status = "error";
            } else if (childStatuses.includes("cancelled")) {
                node.status = "cancelled";
            } else if (childStatuses.every((s) => s === "complete" || s === "skipped")) {
                node.status = childStatuses.every((s) => s === "skipped") ? "skipped" : "complete";
            } else {
                node.status = "ready";
            }
        } else {
            node.selected = false;
            node.partial = false;
            node.status = "ready";
        }
        return node.selected;
    };
    state.roots.forEach((id) => visit(state.nodes.get(id)));
}

function updateSelectAllCheckbox() {
    const files = Array.from(state.files.values());
    const selected = files.filter((file) => file.selected).length;
    els.selectAll.checked = files.length > 0 && selected === files.length;
    els.selectAll.indeterminate = selected > 0 && selected < files.length;
}

function getSelectedFileIds() {
    return Array.from(state.files.values()).filter((file) => file.selected).map((file) => file.id);
}

function updateStats() {
    const files = Array.from(state.files.values());
    const totalFiles = files.length;
    const complete = files.filter((file) => file.status === "complete").length;
    const skipped = files.filter((file) => file.status === "skipped").length;
    const remaining = files.filter((file) => !["complete", "skipped"].includes(file.status)).length;
    const selected = files.filter((file) => file.selected).length;
    
    const activeFiles = files.filter((f) => f.status !== "ready" && f.status !== "skipped");
    const totalSize = activeFiles.reduce((sum, file) => sum + Number(file.size || 0), 0);
    const downloaded = activeFiles.reduce((sum, file) => {
        if (file.size) return sum + Number(file.size) * Math.max(0, Math.min(100, Number(file.progress || 0))) / 100;
        return sum + (file.status === "complete" ? 1 : 0);
    }, 0);
    
    const unknownTotal = activeFiles.some((file) => !file.size);
    const speed = activeFiles.reduce((sum, file) => sum + Number(file.speed || 0), 0);
    const progress = totalSize ? downloaded / totalSize * 100 : (activeFiles.length ? activeFiles.filter(f => f.status === "complete").length / activeFiles.length * 100 : 0);
    const remainingBytes = Math.max(0, totalSize - downloaded);

    statsEls.totalFiles.textContent = totalFiles;
    statsEls.completed.textContent = complete;
    statsEls.skipped.textContent = skipped;
    statsEls.remaining.textContent = remaining;
    statsEls.selected.textContent = selected;
    statsEls.totalSize.textContent = unknownTotal && totalSize === 0 ? "Unknown" : formatBytes(totalSize);
    statsEls.speed.textContent = `${formatBytes(speed)}/s`;
    statsEls.eta.textContent = speed > 0 && remainingBytes > 0 ? formatDuration(remainingBytes / speed) : "--";
    statsEls.progress.textContent = `${Math.round(progress)}%`;
    statsEls.progressBar.style.width = `${Math.max(0, Math.min(100, progress))}%`;
    state.completedCount = complete;
    setBusyControls();
}

function updateElapsed() {
    if (state.downloadStartedAt && state.isDownloading) {
        statsEls.elapsed.textContent = formatDuration((Date.now() - state.downloadStartedAt) / 1000);
    }
}

function addLog(level, message, time = null) {
    const date = time ? new Date(time) : new Date();
    const hhmmss = date.toLocaleTimeString([], { hour12: false });
    const normalized = String(level || "INFO").toUpperCase();
    const line = `[${hhmmss}] [${normalized}] ${message}`;
    state.logs.push(line);
    const entry = document.createElement("div");
    entry.className = `log-entry log-${normalized.toLowerCase()}`;
    entry.innerHTML = `<span class="time">[${hhmmss}]</span> <span class="level">[${normalized}]</span> ${escapeHtml(message)}`;
    els.logViewer.appendChild(entry);
    els.logViewer.scrollTop = els.logViewer.scrollHeight;
}

function updateNetworkStatus() {
    const online = navigator.onLine;
    els.networkDot.className = `dot ${online ? "online" : "offline"}`;
    els.networkLabel.textContent = online ? "Connected" : "Disconnected";
}

function setServerReachable(value) {
    state.serverReachable = value;
    els.serverLabel.classList.remove("server-reachable", "server-unreachable");
    if (value === null) {
        els.serverLabel.textContent = "Server not inspected";
    } else {
        if (value) {
            els.serverLabel.textContent = "Server reachable";
            els.serverLabel.classList.add("server-reachable");
        } else {
            els.serverLabel.textContent = "Server unreachable";
            els.serverLabel.classList.add("server-unreachable");
        }
    }
}

async function updateStorage() {
    try {
        const path = state.config.download_folder || "";
        const payload = await api(`/api/storage?path=${encodeURIComponent(path)}`, { headers: {} });
        const pct = Number(payload.percent || 0);
        const circumference = 2 * Math.PI * 48;
        els.storageRing.style.strokeDasharray = `${circumference * pct / 100} ${circumference}`;
        els.storageRing.style.stroke = pct > 90 ? "var(--red)" : (pct > 80 ? "var(--yellow)" : "var(--green)");
        els.storagePercent.textContent = `${Math.round(pct)}%`;
        els.storageUsed.textContent = `${formatBytes(payload.used)} / ${formatBytes(payload.total)}`;
        els.storageFolder.textContent = `Folder: ${formatBytes(payload.folder_size)}`;
    } catch {
        els.storageFolder.textContent = "Folder: unavailable";
    }
}

function switchView(view) {
    state.currentView = view;
    $$(".nav-item").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view));
    $$(".view").forEach((panel) => panel.classList.toggle("active", panel.id === `view-${view}`));
    if (view === "downloads") loadHistory();
    if (view === "about") loadSystemInfo();
}

function switchTab(tab) {
    state.currentTab = tab;
    $$(".tab").forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tab));
    $("#panel-progress").classList.toggle("active", tab === "progress");
    $("#panel-logs").classList.toggle("active", tab === "logs");
}

function switchSettingsPanel(panel) {
    $$(".settings-nav-item").forEach((button) => {
        button.classList.toggle("active", button.dataset.settingsPanel === panel);
    });
    $$(".settings-panel").forEach((section) => {
        section.classList.toggle("active", section.dataset.settingsPanel === panel);
    });
}

async function startScan() {
    const url = els.urlInput.value.trim();
    els.urlError.textContent = "";
    if (!url) {
        els.urlError.textContent = "Invalid URL format.";
        return;
    }
    if (state.scannedUrl === url && state.files.size > 0) {
        const ok = confirm("You already scanned this URL. Clear results and rescan?");
        if (!ok) return;
    }
    resetTree();
    setServerReachable(null);
    state.scannedUrl = url;
    state.isScanning = true;
    setBusyControls();
    els.activityText.textContent = `Scanning: ${url}`;
    try {
        await api("/api/scan", { method: "POST", body: JSON.stringify({ url }) });
    } catch (error) {
        state.isScanning = false;
        setBusyControls();
        els.urlError.textContent = error.message;
        toast(error.message, "error");
    }
}

async function stopScan() {
    await api("/api/scan/stop", { method: "POST" });
}

async function clearInspection() {
    if (state.isScanning || state.isDownloading) {
        toast("Cannot clear while app is busy", "error");
        return;
    }
    try {
        await api("/api/scan/clear", { method: "POST" });
        els.urlInput.value = "";
        resetTree();
        setServerReachable(null);
        state.scannedUrl = "";
        els.activityText.textContent = "Idle";
        toast("Inspection cleared", "success");
    } catch (error) {
        toast(error.message, "error");
    }
}

async function startDownload(mode) {
    const ids = mode === "all" ? [] : getSelectedFileIds();
    if (mode !== "all" && ids.length === 0) {
        toast("No files selected", "error");
        return;
    }
    try {
        state.isDownloading = true;
        state.isPaused = false;
        state.downloadStartedAt = Date.now();
        setBusyControls();
        await api("/api/download", {
            method: "POST",
            body: JSON.stringify({ mode, ids }),
        });
    } catch (error) {
        state.isDownloading = false;
        setBusyControls();
        toast(error.message, "error");
    }
}

async function togglePause() {
    if (!state.isDownloading) return;
    if (state.isPaused) {
        await api("/api/download/resume", { method: "POST" });
    } else {
        await api("/api/download/pause", { method: "POST" });
    }
}

async function cancelDownload() {
    if (!state.isDownloading) return;
    const ok = confirm("Cancel all downloads?");
    if (!ok) return;
    await api("/api/download/cancel", { method: "POST" });
}

async function skipFile(id) {
    await api("/api/download/skip", {
        method: "POST",
        body: JSON.stringify({ id }),
    });
}

function triggerNotification(title, message, isError = false) {
    const configKey = isError ? "notify_error" : "notify_complete";
    if (state.config[configKey]) {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.show_notification) {
            window.pywebview.api.show_notification(title, message);
        } else if ("Notification" in window) {
            if (Notification.permission === "granted") {
                new Notification(title, { body: message });
            } else if (Notification.permission !== "denied") {
                Notification.requestPermission().then((permission) => {
                    if (permission === "granted") {
                        new Notification(title, { body: message });
                    }
                });
            }
        }
    }
}

function handleEvent(event) {
    switch (event.type) {
        case "hello":
            hydrateState(event.state);
            break;
        case "scan_reset":
            resetTree();
            state.isScanning = true;
            state.scannedUrl = event.url || state.scannedUrl;
            setBusyControls();
            break;
        case "scan_started":
            state.isScanning = true;
            els.activityText.textContent = `Scanning: ${event.url}`;
            setBusyControls();
            break;
        case "folder":
            addFolder(event.path || "");
            break;
        case "file":
            addFile(event.file);
            break;
        case "file_update":
            updateFile(event.file);
            break;
        case "status":
            els.activityText.textContent = event.text || "Working";
            break;
        case "server_status":
            setServerReachable(Boolean(event.reachable));
            break;
        case "log":
            addLog(event.level, event.message, event.time);
            break;
        case "scan_done":
            state.isScanning = false;
            const scannedCount = event.files || 0;
            els.activityText.textContent = `Scan complete. Found ${scannedCount} files (${formatBytes(event.total_size || 0)}). ${scannedCount} selected for download.`;
            toast("Inspection complete", "success");
            refreshFolderSelection();
            renderTree();
            break;
        case "scan_cancelled":
            state.isScanning = false;
            els.activityText.textContent = "Inspection stopped";
            setBusyControls();
            break;
        case "scan_error":
            state.isScanning = false;
            els.activityText.textContent = "Inspection failed";
            toast(event.error || "Scan failed", "error");
            triggerNotification("Inspection Failed", event.error || "A scan error occurred.", true);
            setBusyControls();
            break;
        case "download_started":
            state.isDownloading = true;
            state.isPaused = false;
            state.downloadStartedAt = Date.now();
            els.activityText.textContent = `${event.total} files queued`;
            setBusyControls();
            break;
        case "download_active":
            els.activityText.textContent = `Downloading: ${event.rel_path}`;
            break;
        case "download_progress":
            if (state.files.has(event.file_id)) {
                const file = state.files.get(event.file_id);
                file.progress = Number(event.progress || 0);
                file.speed = Number(event.speed || 0);
                file.downloaded = Number(event.downloaded || 0);
                if (event.size) file.size = event.size;
                renderTree();
                updateStats();
            }
            break;
        case "download_summary":
            state.completedCount = event.completed || 0;
            state.skippedCount = event.skipped || 0;
            state.failedCount = event.failed || 0;
            break;
        case "download_paused":
            state.isPaused = true;
            els.activityText.textContent = "Paused";
            setBusyControls();
            break;
        case "download_resumed":
            state.isPaused = false;
            els.activityText.textContent = "Resumed";
            setBusyControls();
            break;
        case "download_done":
            state.isDownloading = false;
            state.isPaused = false;
            els.activityText.textContent = `Complete! ${event.files_completed || 0} files downloaded.`;
            setBusyControls();
            updateStorage();
            loadHistory();
            if (event.files_failed > 0) {
                triggerNotification("Download Queue Completed with Errors", `Complete! ${event.files_completed || 0} files downloaded, but ${event.files_failed} files failed.`, true);
                playSoundAlert("error");
            } else {
                triggerNotification("File Downloader by Faysal", "Download session finished.");
                playSoundAlert("success");
            }
            if (state.config.auto_close) {
                if (window.pywebview?.api?.close_app) {
                    window.pywebview.api.close_app();
                } else {
                    window.close();
                }
            }
            toast("Download session finished", "success");
            break;
        case "config_updated":
            state.config = event.config;
            applyConfigToForm(state.config);
            applyAppearance();
            updateStorage();
            break;
        case "history_updated":
            loadHistory();
            break;
        default:
            break;
    }
}

function hydrateState(snapshot) {
    if (!snapshot) return;
    state.scannedUrl = snapshot.scanned_url !== undefined ? snapshot.scanned_url : state.scannedUrl;
    state.isScanning = Boolean(snapshot.is_scanning);
    state.isDownloading = Boolean(snapshot.is_downloading);
    state.isPaused = Boolean(snapshot.is_paused);
    resetTree();
    (snapshot.folders || []).forEach((folder) => addFolder(folder));
    (snapshot.files || []).forEach((file) => addFile(file));
    if (!state.scannedUrl) {
        els.urlInput.value = "";
        els.activityText.textContent = "Idle";
    }
    setBusyControls();
}

function connectEvents() {
    const source = new EventSource("/api/stream");
    source.onmessage = (message) => {
        try {
            handleEvent(JSON.parse(message.data));
        } catch (error) {
            console.error("Bad SSE event", error, message.data);
        }
    };
    source.onerror = () => {
        setTimeout(() => {
            source.close();
            connectEvents();
        }, 2000);
    };
}

function renderHistory() {
    const query = els.historySearch.value.trim().toLowerCase();
    const rows = state.history
        .filter((item) => !query || JSON.stringify(item).toLowerCase().includes(query))
        .sort((a, b) => {
            const key = state.historySort.key;
            const dir = state.historySort.dir === "asc" ? 1 : -1;
            return String(a[key] ?? "").localeCompare(String(b[key] ?? ""), undefined, { numeric: true }) * dir;
        });

    els.historyBody.innerHTML = rows.map((item) => `
        <tr>
            <td>${escapeHtml(new Date(item.date).toLocaleString())}</td>
            <td><div class="history-url" title="${escapeHtml(item.source_url)}">${escapeHtml(item.source_url || "—")}</div></td>
            <td>${item.files_completed || 0}/${item.files_total || 0}</td>
            <td>${formatBytes(item.total_size || 0)}</td>
            <td>${formatDuration(item.duration || 0)}</td>
            <td>${escapeHtml(item.status || "—")}</td>
            <td>
                <div class="history-actions">
                    <button class="btn secondary skip-row-btn" data-history-action="redownload" data-url="${escapeHtml(item.source_url || "")}">Re-download</button>
                    <button class="btn secondary skip-row-btn" data-history-action="open" data-path="${escapeHtml(item.output_dir || "")}">Open Folder</button>
                    <button class="btn danger skip-row-btn" data-history-action="delete" data-id="${escapeHtml(item.id || "")}">Delete</button>
                </div>
            </td>
        </tr>
    `).join("");
    els.historyEmpty.classList.toggle("hidden", rows.length > 0);
}

async function loadHistory() {
    const payload = await api("/api/history");
    state.history = payload.history || [];
    renderHistory();
}

async function loadSystemInfo() {
    const payload = await api("/api/system");
    els.aboutVersion.textContent = `Version ${payload.version}`;
    const entries = {
        Developer: payload.developer,
        License: payload.license,
        OS: payload.os,
        Python: payload.python,
        "Config File": payload.config_path,
        "Download Folder": payload.download_folder,
        "Disk Free": formatBytes(payload.disk_free),
        "Disk Total": formatBytes(payload.disk_total),
    };
    els.systemList.innerHTML = Object.entries(entries)
        .map(([key, value]) => `
            <div class="system-item">
                <span class="label">${escapeHtml(key)}</span>
                <span class="value">${escapeHtml(value)}</span>
            </div>
        `)
        .join("");
}

async function openFolder(path) {
    const target = path || settingEls.download_folder.value;
    if (window.pywebview?.api?.open_path) {
        await window.pywebview.api.open_path(target);
    } else {
        await api("/api/open_path", { method: "POST", body: JSON.stringify({ path: target }) });
    }
}

async function browseFolder() {
    if (window.pywebview?.api?.select_folder) {
        const selected = await window.pywebview.api.select_folder(settingEls.download_folder.value);
        if (selected) settingEls.download_folder.value = selected;
        return;
    }
    const selected = prompt("Download folder", settingEls.download_folder.value);
    if (selected) settingEls.download_folder.value = selected;
}

function attachEvents() {
    $$(".nav-item").forEach((btn) => btn.addEventListener("click", () => switchView(btn.dataset.view)));
    $$(".tab").forEach((btn) => btn.addEventListener("click", () => switchTab(btn.dataset.tab)));
    $$(".settings-nav-item").forEach((btn) => {
        btn.addEventListener("click", () => switchSettingsPanel(btn.dataset.settingsPanel));
    });
    $$("[data-choice-for] button[data-value]").forEach((button) => {
        button.addEventListener("click", () => {
            updateConfigPreview(button.closest("[data-choice-for]").dataset.choiceFor, button.dataset.value);
        });
    });
    els.paletteGrid.addEventListener("click", (event) => {
        const button = event.target.closest(".palette-option");
        if (!button) return;
        const palette = palettes[button.dataset.palette] || palettes.violet;
        state.config = {
            ...state.config,
            appearance_preset: button.dataset.palette,
            accent_color: palette.accent,
        };
        if (settingEls.appearance_preset) {
            settingEls.appearance_preset.value = button.dataset.palette;
        }
        applyAppearance();
        syncChoiceButtons();
        saveSettings();
    });
    const systemTheme = window.matchMedia?.("(prefers-color-scheme: light)");
    systemTheme?.addEventListener?.("change", () => {
        if (state.config.theme === "system") applyAppearance();
    });

    els.inspectBtn.addEventListener("click", startScan);
    els.urlInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") startScan();
    });
    els.stopScanBtn.addEventListener("click", stopScan);
    els.clearInspectBtn.addEventListener("click", clearInspection);
    els.downloadSelectedBtn.addEventListener("click", () => startDownload("selected"));
    els.downloadAllBtn.addEventListener("click", () => startDownload("all"));
    els.pauseBtn.addEventListener("click", togglePause);
    els.cancelBtn.addEventListener("click", cancelDownload);
    els.clearSelectionBtn.addEventListener("click", () => {
        state.files.forEach((file) => { file.selected = false; });
        refreshFolderSelection();
        renderTree();
        updateActivityTextSelection();
    });
    els.selectAll.addEventListener("change", () => {
        state.files.forEach((file) => { file.selected = els.selectAll.checked; });
        state.nodes.forEach((node) => {
            if (node.type === "folder") {
                node.selected = els.selectAll.checked;
                node.partial = false;
            }
        });
        renderTree();
        updateActivityTextSelection();
    });

    els.fileBody.addEventListener("click", (event) => {
        const target = event.target.closest("button");
        if (!target) return;
        if (target.dataset.action === "toggle-folder") {
            const node = state.nodes.get(target.dataset.id);
            if (node) {
                node.expanded = !node.expanded;
                renderTree();
            }
        }
        if (target.dataset.action === "skip-file") {
            skipFile(target.dataset.id);
        }
    });
    els.fileBody.addEventListener("change", (event) => {
        if (!event.target.matches("input[data-node-id]")) return;
        setNodeSelection(event.target.dataset.nodeId, event.target.checked);
        refreshFolderSelection();
        renderTree();
        updateActivityTextSelection();
    });
    els.fileBody.addEventListener("dblclick", (event) => {
        const rowName = event.target.closest(".row-name");
        if (rowName) {
            const tr = rowName.closest("tr");
            const nodeId = tr?.dataset.id;
            const node = state.nodes.get(nodeId);
            if (node) {
                node.expandedName = !node.expandedName;
                renderTree();
            }
        }
    });

    els.clearLogBtn.addEventListener("click", () => {
        state.logs = [];
        els.logViewer.innerHTML = "";
    });
    els.copyLogBtn.addEventListener("click", async () => {
        await navigator.clipboard.writeText(state.logs.join("\n"));
        toast("Log copied", "success");
    });
    els.exportLogBtn.addEventListener("click", async () => {
        const text = state.logs.join("\n");
        if (window.pywebview?.api?.export_logs) {
            const success = await window.pywebview.api.export_logs(text);
            if (success) toast("Log exported successfully", "success");
        } else {
            const blob = new Blob([text], { type: "text/plain" });
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = `file-downloader-log-${Date.now()}.txt`;
            link.click();
            URL.revokeObjectURL(link.href);
        }
    });

    els.saveSettingsBtn.addEventListener("click", saveSettings);
    els.resetSettingsBtn.addEventListener("click", async () => {
        const payload = await api("/api/config/reset", { method: "POST" });
        state.config = payload.config;
        applyConfigToForm(state.config);
        applyAppearance();
        toast("Defaults restored", "success");
    });
    els.browseFolderBtn.addEventListener("click", browseFolder);
    els.openFolderBtn.addEventListener("click", () => openFolder(settingEls.download_folder.value));

    els.historySearch.addEventListener("input", renderHistory);
    els.refreshHistoryBtn.addEventListener("click", loadHistory);
    els.clearHistoryBtn.addEventListener("click", async () => {
        if (!confirm("Clear download history?")) return;
        await api("/api/history", { method: "DELETE" });
        state.history = [];
        renderHistory();
    });
    $(".history-table").addEventListener("click", async (event) => {
        const header = event.target.closest("th[data-sort]");
        if (header) {
            if (state.historySort.key === header.dataset.sort) {
                state.historySort.dir = state.historySort.dir === "asc" ? "desc" : "asc";
            } else {
                state.historySort = { key: header.dataset.sort, dir: "asc" };
            }
            renderHistory();
            return;
        }
        const button = event.target.closest("button[data-history-action]");
        if (!button) return;
        if (button.dataset.historyAction === "redownload") {
            switchView("home");
            els.urlInput.value = button.dataset.url || "";
            startScan();
        } else if (button.dataset.historyAction === "open") {
            await openFolder(button.dataset.path);
        } else if (button.dataset.historyAction === "delete") {
            await api(`/api/history/${button.dataset.id}`, { method: "DELETE" });
            await loadHistory();
        }
    });

    let currentUpdateInfo = null;

    window.updateProgress = (percent, text) => {
        if (percent === -2) {
            $("#update-progress-container").classList.add("hidden");
            $("#update-now-btn").classList.remove("hidden");
            $("#update-now-btn").disabled = false;
            $("#update-later-btn").classList.remove("hidden");
            $("#update-later-btn").disabled = false;
            $("#update-cancel-btn").classList.add("hidden");
            toast("Update cancelled", "warning");
            return;
        }
        if (percent === -1) {
            $("#update-now-btn").classList.remove("hidden");
            $("#update-now-btn").disabled = false;
            $("#update-later-btn").classList.remove("hidden");
            $("#update-later-btn").disabled = false;
            $("#update-cancel-btn").classList.add("hidden");
            toast(text, "error");
            return;
        }
        $("#update-progress-container").classList.remove("hidden");
        $("#update-progress-fill").style.width = `${percent}%`;
        $("#update-status").textContent = text;
    };

    $("#report-bug-btn").addEventListener("click", () => {
        const mailtoUrl = "mailto:faysalahmmed4200@gmail.com?subject=File%20Downloader%20by%20Faysal%20Bug%20Report";
        if (window.pywebview?.api?.open_url) {
            window.pywebview.api.open_url(mailtoUrl);
        } else {
            window.open(mailtoUrl, "_blank");
        }
    });

    $("#check-updates-btn").addEventListener("click", async () => {
        if (!window.pywebview?.api?.check_for_updates) {
            toast("Updater is only available in the desktop app", "error");
            return;
        }
        const btn = $("#check-updates-btn");
        btn.disabled = true;
        btn.textContent = "Checking...";
        try {
            const info = await window.pywebview.api.check_for_updates();
            if (info.update_available) {
                currentUpdateInfo = info;
                $("#update-title").textContent = `Update Available: ${info.version}`;
                $("#update-desc").textContent = `A new version of File Downloader by Faysal is available for your system.`;
                $("#update-now-btn").classList.remove("hidden");
                $("#update-now-btn").disabled = false;
                $("#update-later-btn").classList.remove("hidden");
                $("#update-later-btn").disabled = false;
                $("#update-cancel-btn").classList.add("hidden");
                $("#update-progress-container").classList.add("hidden");
                $("#update-modal").classList.remove("hidden");
            } else {
                if (info.error) toast(`Update check failed: ${info.error}`, "error");
                else toast("You are on the latest version", "success");
            }
        } catch (e) {
            toast("Failed to check for updates", "error");
        } finally {
            btn.disabled = false;
            btn.textContent = "Check for Updates";
        }
    });

    $("#update-now-btn").addEventListener("click", () => {
        if (!currentUpdateInfo) return;
        $("#update-now-btn").classList.add("hidden");
        $("#update-later-btn").classList.add("hidden");
        $("#update-cancel-btn").classList.remove("hidden");
        $("#update-cancel-btn").disabled = false;
        $("#update-progress-container").classList.remove("hidden");
        $("#update-progress-fill").style.width = "0%";
        $("#update-status").textContent = "Connecting...";
        window.pywebview.api.perform_update(currentUpdateInfo);
    });

    $("#update-later-btn").addEventListener("click", () => {
        $("#update-modal").classList.add("hidden");
        $("#update-now-btn").classList.remove("hidden");
        $("#update-now-btn").disabled = false;
        $("#update-later-btn").classList.remove("hidden");
        $("#update-later-btn").disabled = false;
        $("#update-cancel-btn").classList.add("hidden");
        $("#update-progress-container").classList.add("hidden");
    });

    $("#update-cancel-btn").addEventListener("click", () => {
        $("#update-cancel-btn").disabled = true;
        $("#update-status").textContent = "Cancelling...";
        if (window.pywebview?.api?.cancel_update) {
            window.pywebview.api.cancel_update();
        }
    });

    window.addEventListener("online", updateNetworkStatus);
    window.addEventListener("offline", updateNetworkStatus);
    document.addEventListener("keydown", (event) => {
        const meta = event.ctrlKey || event.metaKey;
        if (meta && event.key.toLowerCase() === "a") {
            event.preventDefault();
            els.selectAll.checked = true;
            els.selectAll.dispatchEvent(new Event("change"));
        }
        if (meta && event.key.toLowerCase() === "d") {
            event.preventDefault();
            startDownload("selected");
        }
        if (meta && event.key.toLowerCase() === "l") {
            event.preventDefault();
            switchView("home");
            switchTab("logs");
        }
        if (meta && event.key === ",") {
            event.preventDefault();
            switchView("settings");
        }
        if (event.key === "Escape") {
            if (state.isScanning) stopScan();
            if (state.isDownloading) cancelDownload();
        }
        if (event.key === " " && state.isDownloading && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
            event.preventDefault();
            togglePause();
        }
    });
}

async function requestNotificationPermission() {
    if ("Notification" in window && Notification.permission === "default") {
        try {
            await Notification.requestPermission();
        } catch {
            // Some embedded webviews do not expose notifications.
        }
    }
}

async function init() {
    renderPaletteGrid();
    attachEvents();
    updateNetworkStatus();
    setServerReachable(null);
    resetTree();
    connectEvents();
    await loadConfig();
    await loadHistory();
    await loadSystemInfo();
    await requestNotificationPermission();
    setInterval(updateElapsed, 1000);
    setInterval(updateStorage, 5000);
    addLog("SYSTEM", "File Downloader by Faysal ready.");
}

init().catch((error) => {
    console.error(error);
    toast(error.message || "Startup failed", "error");
});
