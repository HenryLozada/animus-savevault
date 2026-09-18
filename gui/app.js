// ANIMUS // ABSTERGO INDUSTRIES SAVEVAULT - FRONTEND CONTROLLER V4.0
// Memory Matrix, Cloud Synchronization & Telemetry Engine

let allGames = [];
let filteredGames = [];
let currentFilter = "all";
let backupsList = [];
let cloudProviders = [];
let schedulerConfig = {};
const selectedGamePaths = new Set();

// Elementos DOM
const elements = {
  // Navigation Tabs
  navTabs: document.querySelectorAll(".nav-tab"),
  viewPanels: {
    memory: document.getElementById("view-memory"),
    analytics: document.getElementById("view-analytics"),
    cloud: document.getElementById("view-cloud")
  },

  // Header & Controls
  btnScan: document.getElementById("btn-scan"),
  scanIcon: document.getElementById("scan-icon"),
  scanSpinner: document.getElementById("scan-spinner"),
  scanBtnText: document.getElementById("scan-btn-text"),
  btnRestoreMaster: document.getElementById("btn-restore-master"),
  btnOpenBackupsFolder: document.getElementById("btn-open-backups-folder"),
  backupsCount: document.getElementById("backups-count"),

  // Telemetry Bar
  statGames: document.getElementById("stat-games"),
  statSize: document.getElementById("stat-size"),
  statFiles: document.getElementById("stat-files"),
  statCloudStatus: document.getElementById("stat-cloud-status"),

  // Memory Matrix Tab
  searchInput: document.getElementById("search-input"),
  searchClear: document.getElementById("search-clear"),
  filterChips: document.getElementById("filter-chips"),
  countAll: document.getElementById("count-all"),
  countEpic: document.getElementById("count-epic"),
  countSteam: document.getElementById("count-steam"),
  countEa: document.getElementById("count-ea"),
  countUbi: document.getElementById("count-ubi"),
  countGog: document.getElementById("count-gog"),
  countXbox: document.getElementById("count-xbox"),
  countRepack: document.getElementById("count-repack"),
  countSavedgames: document.getElementById("count-savedgames"),
  countDocs: document.getElementById("count-docs"),
  countIndie: document.getElementById("count-indie"),
  btnSelectAll: document.getElementById("btn-select-all"),
  btnDeselectAll: document.getElementById("btn-deselect-all"),
  batchSelectionInfo: document.getElementById("batch-selection-info"),
  btnMasterBackup: document.getElementById("btn-master-backup"),
  gamesGrid: document.getElementById("games-grid"),
  loadingState: document.getElementById("loading-state"),
  emptyState: document.getElementById("empty-state"),

  // Analytics Tab
  analyticsTopStorage: document.getElementById("analytics-top-storage"),
  analyticsRecentActivity: document.getElementById("analytics-recent-activity"),
  analyticsPlatformDist: document.getElementById("analytics-platform-dist"),
  analyticsExtensions: document.getElementById("analytics-extensions"),

  // Cloud & Scheduler Tab
  cloudProvidersContainer: document.getElementById("cloud-providers-container"),
  customCloudInput: document.getElementById("custom-cloud-input"),
  btnBrowseCloudFolder: document.getElementById("btn-browse-cloud-folder"),
  btnSyncCloudNow: document.getElementById("btn-sync-cloud-now"),
  schedulerToggle: document.getElementById("scheduler-toggle"),
  intervalChips: document.getElementById("interval-chips"),
  schedulerLastRun: document.getElementById("scheduler-last-run"),
  schedulerStatusText: document.getElementById("scheduler-status-text"),
  btnSaveScheduler: document.getElementById("btn-save-scheduler"),
  btnTriggerAutoNow: document.getElementById("btn-trigger-auto-now"),

  // Modals & Toast
  backupsModal: document.getElementById("backups-modal"),
  modalClose: document.getElementById("modal-close"),
  btnModalClose: document.getElementById("btn-modal-close"),
  btnModalOpenFolder: document.getElementById("btn-modal-open-folder"),
  modalBackupsList: document.getElementById("backups-list"),
  backupsFilterInput: document.getElementById("backups-filter-input"),

  restoreResultModal: document.getElementById("restore-result-modal"),
  restoreModalClose: document.getElementById("restore-modal-close"),
  btnRestoreModalClose: document.getElementById("btn-restore-modal-close"),
  restoreSummaryText: document.getElementById("restore-summary-text"),
  restoreGamesList: document.getElementById("restore-games-list"),

  // Version History Modal
  versionHistoryModal: document.getElementById("version-history-modal"),
  versionModalClose: document.getElementById("version-modal-close"),
  btnVersionModalClose: document.getElementById("btn-version-modal-close"),
  btnVersionModalOpenFolder: document.getElementById("btn-version-modal-open-folder"),
  versionModalHero: document.getElementById("version-modal-hero"),
  versionModalHeroImg: document.getElementById("version-modal-hero-img"),
  versionModalGameTitle: document.getElementById("version-modal-game-title"),
  versionModalGamePath: document.getElementById("version-modal-game-path"),
  inputVersionNote: document.getElementById("input-version-note"),
  btnCreateVersionSnapshot: document.getElementById("btn-create-version-snapshot"),
  versionTimelineList: document.getElementById("version-timeline-list"),
  versionCountLabel: document.getElementById("version-count-label"),
  versionEmptyState: document.getElementById("version-empty-state"),

  toast: document.getElementById("toast")
};

let currentGameForHistory = null;
let versionCounts = {};
let currentGameVersions = [];

// HUD Toast Notification
function showToast(message, duration = 3800) {
  elements.toast.textContent = `// ${message}`;
  elements.toast.classList.remove("hidden");
  clearTimeout(elements.toast._timer);
  elements.toast._timer = setTimeout(() => {
    elements.toast.classList.add("hidden");
  }, duration);
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + " GB";
}

function getPlatformBadgeClass(platform) {
  const p = platform.toLowerCase();
  if (p.includes("steam") && !p.includes("repack")) return "badge-steam";
  if (p.includes("epic")) return "badge-epic";
  if (p.includes("ea app") || p.includes("electronic arts") || p.includes("origin")) return "badge-ea";
  if (p.includes("ubisoft")) return "badge-ubisoft";
  if (p.includes("gog")) return "badge-gog";
  if (p.includes("xbox") || p.includes("game pass")) return "badge-xbox";
  if (p.includes("repack") || p.includes("codex") || p.includes("rune") || p.includes("goldberg") || p.includes("flt") || p.includes("skidrow") || p.includes("empress")) return "badge-repack";
  if (p.includes("saved games")) return "badge-savedgames";
  if (p.includes("documentos") || p.includes("documents")) return "badge-docs";
  return "badge-generic";
}

function matchesFilter(game, filter) {
  const p = game.platform.toLowerCase();
  switch (filter) {
    case "repack":
      return p.includes("repack") || p.includes("codex") || p.includes("rune") || p.includes("goldberg") || p.includes("flt") || p.includes("skidrow") || p.includes("empress");
    case "steam":
      return p.includes("steam") && !p.includes("repack");
    case "epic":
      return p.includes("epic");
    case "ea":
      return p.includes("ea app") || p.includes("electronic arts") || p.includes("origin");
    case "ubi":
      return p.includes("ubisoft");
    case "gog":
      return p.includes("gog");
    case "xbox":
      return p.includes("xbox") || p.includes("game pass");
    case "savedgames":
      return p.includes("saved games");
    case "docs":
      return p.includes("documentos") || p.includes("documents");
    case "indie":
      return p.includes("locallow") || p.includes("unity") || p.includes("indie");
    case "all":
    default:
      return true;
  }
}

// -------------------------------------------------------------
// TAB SWITCHING CONTROLLER
// -------------------------------------------------------------
function switchTab(tabId) {
  elements.navTabs.forEach(t => t.classList.toggle("active", t.dataset.tab === tabId));
  Object.keys(elements.viewPanels).forEach(k => {
    elements.viewPanels[k].classList.toggle("hidden", k !== tabId);
    elements.viewPanels[k].classList.toggle("active", k === tabId);
  });

  if (tabId === "analytics") {
    loadAnalytics();
  } else if (tabId === "cloud") {
    loadCloudAndScheduler();
  }
}

// -------------------------------------------------------------
// MEMORY MATRIX VIEW
// -------------------------------------------------------------
function updateFilterCounts() {
  let repackCount = 0;
  let steamCount = 0;
  let epicCount = 0;
  let eaCount = 0;
  let ubiCount = 0;
  let gogCount = 0;
  let xboxCount = 0;
  let savedgamesCount = 0;
  let docsCount = 0;
  let indieCount = 0;

  allGames.forEach(g => {
    if (matchesFilter(g, "repack")) repackCount++;
    if (matchesFilter(g, "steam")) steamCount++;
    if (matchesFilter(g, "epic")) epicCount++;
    if (matchesFilter(g, "ea")) eaCount++;
    if (matchesFilter(g, "ubi")) ubiCount++;
    if (matchesFilter(g, "gog")) gogCount++;
    if (matchesFilter(g, "xbox")) xboxCount++;
    if (matchesFilter(g, "savedgames")) savedgamesCount++;
    if (matchesFilter(g, "docs")) docsCount++;
    if (matchesFilter(g, "indie")) indieCount++;
  });

  if (elements.countAll) elements.countAll.textContent = allGames.length;
  if (elements.countEpic) elements.countEpic.textContent = epicCount;
  if (elements.countSteam) elements.countSteam.textContent = steamCount;
  if (elements.countEa) elements.countEa.textContent = eaCount;
  if (elements.countUbi) elements.countUbi.textContent = ubiCount;
  if (elements.countGog) elements.countGog.textContent = gogCount;
  if (elements.countXbox) elements.countXbox.textContent = xboxCount;
  if (elements.countRepack) elements.countRepack.textContent = repackCount;
  if (elements.countSavedgames) elements.countSavedgames.textContent = savedgamesCount;
  if (elements.countDocs) elements.countDocs.textContent = docsCount;
  if (elements.countIndie) elements.countIndie.textContent = indieCount;
}

function updateStats(games) {
  elements.statGames.textContent = games.length;
  const totalBytes = games.reduce((acc, g) => acc + (g.total_size || 0), 0);
  const totalFiles = games.reduce((acc, g) => acc + (g.file_count || 0), 0);
  elements.statSize.textContent = formatBytes(totalBytes);
  elements.statFiles.textContent = totalFiles.toLocaleString();
}

function updateSelectionBar() {
  const count = selectedGamePaths.size;
  if (count === 0) {
    elements.batchSelectionInfo.textContent = "0 BLOQUES MARCADOS";
    elements.btnMasterBackup.disabled = true;
  } else {
    let selectedBytes = 0;
    allGames.forEach(g => {
      if (selectedGamePaths.has(g.path)) {
        selectedBytes += (g.total_size || 0);
      }
    });
    elements.batchSelectionInfo.textContent = `${count} MARCADOS [${formatBytes(selectedBytes)}]`;
    elements.btnMasterBackup.disabled = false;
  }
}

async function refreshVersionCounts() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.get_version_counts) {
    try {
      versionCounts = await window.pywebview.api.get_version_counts() || {};
      document.querySelectorAll(".history-count-badge").forEach(badge => {
        const p = badge.dataset.path;
        const n = badge.dataset.name;
        const normName = n ? n.toLowerCase().replace(/[^a-z0-9]/g, "") : "";
        const safeName = n ? n.replace(/[<>:"/\\|?*]/g, "_").toLowerCase() : "";
        const pathKey = p ? p.toLowerCase() : "";
        const c = versionCounts[normName] || versionCounts[safeName] || versionCounts[pathKey] || 0;
        badge.textContent = `(${c})`;
      });
    } catch (e) {
      console.error("Error consultando version counts:", e);
    }
  }
}

// -------------------------------------------------------------
// CONTROLADOR DE IMÁGENES EN ALTA RESOLUCIÓN Y FALLBACKS
// -------------------------------------------------------------
function handleImageFallback(img) {
  const capsule = img.getAttribute("data-capsule");
  const header = img.getAttribute("data-header");
  const procedural = img.getAttribute("data-procedural");
  const currentSrc = img.src;

  // 1. Probar Cápsula retina de alta resolución (616x353)
  if (capsule && currentSrc !== capsule && !img.dataset.triedCapsule) {
    img.dataset.triedCapsule = "true";
    img.src = capsule;
    return;
  }
  // 2. Probar Header oficial de Steam (460x215)
  if (header && currentSrc !== header && !img.dataset.triedHeader) {
    img.dataset.triedHeader = "true";
    img.src = header;
    return;
  }
  // 3. Fallback garantizado: SVG holográfico procedimental Animus (cero espacios vacíos)
  if (procedural && currentSrc !== procedural) {
    img.src = procedural;
  }
}

function renderGames() {
  elements.gamesGrid.innerHTML = "";

  if (filteredGames.length === 0) {
    elements.emptyState.classList.remove("hidden");
    return;
  }
  elements.emptyState.classList.add("hidden");

  const fragment = document.createDocumentFragment();

  filteredGames.forEach((game) => {
    const isSelected = selectedGamePaths.has(game.path);
    const card = document.createElement("div");
    card.className = `memory-card ${isSelected ? 'selected' : ''}`;
    card.dataset.path = game.path;

    const badgeClass = getPlatformBadgeClass(game.platform);
    const extensionsHtml = (game.extensions || [])
      .slice(0, 5)
      .map(ext => `<span class="ext-badge">${ext}</span>`)
      .join("");

    const normName = game.name.toLowerCase().replace(/[^a-z0-9]/g, "");
    const safeName = game.name.replace(/[<>:"/\\|?*]/g, "_").toLowerCase();
    const pathKey = game.path.toLowerCase();
    const vCount = versionCounts[normName] || versionCounts[safeName] || versionCounts[pathKey] || 0;

    const primaryImg = game.image_url || game.capsule_url || game.procedural_banner || "";
    const capsuleImg = game.capsule_url || "";
    const headerImg = game.header_url || "";
    const proceduralImg = game.procedural_banner || "";

    card.innerHTML = `
      <div class="card-media-banner">
        <img
          class="game-cover-art"
          src="${primaryImg}"
          data-capsule="${capsuleImg}"
          data-header="${headerImg}"
          data-procedural="${proceduralImg}"
          alt="${game.name}"
          loading="lazy"
          onerror="handleImageFallback(this)"
        />
        <div class="media-banner-overlay"></div>
        <div class="media-top-bar">
          <label class="hud-checkbox-label" title="Seleccionar bloque de memoria">
            <input type="checkbox" class="hud-checkbox" data-path="${game.path}" ${isSelected ? 'checked' : ''} />
          </label>
          <span class="badge-sector ${badgeClass}">${game.platform}</span>
        </div>
        <div class="media-title-bar">
          <h3 class="game-name" title="${game.name}">${game.name}</h3>
        </div>
      </div>

      <div class="card-body">
        <div class="memory-address-box" title="${game.path}">
          <span class="address-text">${game.path}</span>
          <button class="btn-copy-address" data-path="${game.path}" title="Copiar dirección al portapapeles">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          </button>
        </div>

        <div class="card-telemetry">
          <span>ARCHIVOS: <strong>${game.file_count}</strong></span>
          <span>TAMAÑO: <strong>${game.size_str}</strong></span>
          <span>MODIFICADO: <strong>${game.last_modified}</strong></span>
        </div>

        ${extensionsHtml ? `<div class="memory-extensions">${extensionsHtml}</div>` : ""}

        <div class="card-actions-row">
          <button class="btn-card-action" data-action="open" data-path="${game.path}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
            EXPLORAR
          </button>
          <button class="btn-card-action btn-card-history" data-action="history" data-path="${game.path}" data-name="${game.name}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            HISTORIAL <span class="history-count-badge" data-path="${game.path}" data-name="${game.name}">(${vCount})</span>
          </button>
          <button class="btn-card-action btn-card-backup" data-action="backup" data-path="${game.path}" data-name="${game.name}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
            RESPALDO .ZIP
          </button>
        </div>
      </div>
    `;

    fragment.appendChild(card);
  });

  elements.gamesGrid.appendChild(fragment);
  updateSelectionBar();
}

function applyFilters() {
  const query = elements.searchInput.value.toLowerCase().trim();

  if (query) {
    elements.searchClear.classList.remove("hidden");
  } else {
    elements.searchClear.classList.add("hidden");
  }

  filteredGames = allGames.filter(game => {
    const matchesCat = matchesFilter(game, currentFilter);
    if (!matchesCat) return false;

    if (!query) return true;

    const nameMatch = game.name.toLowerCase().includes(query);
    const pathMatch = game.path.toLowerCase().includes(query);
    const platMatch = game.platform.toLowerCase().includes(query);
    const extMatch = (game.extensions || []).some(ext => ext.toLowerCase().includes(query));

    return nameMatch || pathMatch || platMatch || extMatch;
  });

  updateStats(filteredGames);
  renderGames();
}

async function triggerScan() {
  elements.btnScan.disabled = true;
  elements.scanIcon.classList.add("hidden");
  elements.scanSpinner.classList.remove("hidden");
  elements.scanBtnText.textContent = "SINCRONIZANDO...";
  elements.gamesGrid.innerHTML = "";
  elements.emptyState.classList.add("hidden");
  elements.loadingState.classList.remove("hidden");

  try {
    if (window.pywebview && window.pywebview.api) {
      const results = await window.pywebview.api.scan_games();
      allGames = results || [];
    }
  } catch (err) {
    showToast("Error de sincronización: " + err);
  } finally {
    elements.loadingState.classList.add("hidden");
    elements.scanSpinner.classList.add("hidden");
    elements.scanIcon.classList.remove("hidden");
    elements.scanBtnText.textContent = "SINCRONIZAR";
    elements.btnScan.disabled = false;

    await refreshVersionCounts();
    updateFilterCounts();
    applyFilters();
    refreshBackupsCount();
    showToast(`SINCRONIZACIÓN EXITOSA: ${allGames.length} BLOQUES DETECTADOS`);
  }
}

// -------------------------------------------------------------
// TELEMETRY & ANALYTICS CONTROLLER
// -------------------------------------------------------------
async function loadAnalytics() {
  if (!window.pywebview || !window.pywebview.api) return;

  try {
    const data = await window.pywebview.api.get_analytics(allGames);

    // 1. Top Storage Bars
    elements.analyticsTopStorage.innerHTML = "";
    (data.top_storage || []).forEach(item => {
      const row = document.createElement("div");
      row.className = "storage-row";
      row.innerHTML = `
        <div class="storage-meta">
          <span>${item.name} [${item.platform}]</span>
          <strong>${item.size_str} (${item.percentage}%)</strong>
        </div>
        <div class="storage-bar-track">
          <div class="storage-bar-fill" style="width: ${Math.max(4, item.percentage)}%"></div>
        </div>
      `;
      elements.analyticsTopStorage.appendChild(row);
    });

    // 2. Recent Activity
    elements.analyticsRecentActivity.innerHTML = "";
    (data.recent_activity || []).forEach(item => {
      const row = document.createElement("div");
      row.className = "activity-row";
      row.innerHTML = `
        <div>
          <div class="activity-game">${item.name}</div>
          <div class="activity-date">SECTOR: ${item.platform}</div>
        </div>
        <div class="activity-date text-cyan">${item.last_modified}</div>
      `;
      elements.analyticsRecentActivity.appendChild(row);
    });

    // 3. Platform Distribution
    elements.analyticsPlatformDist.innerHTML = "";
    const distGrid = document.createElement("div");
    distGrid.className = "platform-dist-grid";
    (data.platform_distribution || []).forEach(p => {
      const card = document.createElement("div");
      card.className = "dist-card";
      card.innerHTML = `
        <span class="dist-label">${p.category}</span>
        <span class="dist-value">${p.count} <small style="font-size: 11px; color: var(--hud-gray);">(${p.percentage}%)</small></span>
      `;
      distGrid.appendChild(card);
    });
    elements.analyticsPlatformDist.appendChild(distGrid);

    // 4. Extensions
    elements.analyticsExtensions.innerHTML = "";
    const extMatrix = document.createElement("div");
    extMatrix.className = "extensions-matrix";
    (data.extension_stats || []).forEach(ext => {
      const tag = document.createElement("div");
      tag.className = "ext-matrix-tag";
      tag.innerHTML = `
        <span>${ext.extension}</span>
        <span class="ext-matrix-count">${ext.count}</span>
      `;
      extMatrix.appendChild(tag);
    });
    elements.analyticsExtensions.appendChild(extMatrix);

  } catch (err) {
    console.error("Error al cargar analytics:", err);
  }
}

// -------------------------------------------------------------
// CLOUD & SCHEDULER CONTROLLER
// -------------------------------------------------------------
async function loadCloudAndScheduler() {
  if (!window.pywebview || !window.pywebview.api) return;

  try {
    cloudProviders = await window.pywebview.api.get_cloud_providers();
    schedulerConfig = await window.pywebview.api.get_scheduler_config();

    renderCloudProviders();
    renderSchedulerConfig();
  } catch (err) {
    console.error("Error cargando nube y scheduler:", err);
  }
}

function renderCloudProviders() {
  elements.cloudProvidersContainer.innerHTML = "";

  if (!cloudProviders || cloudProviders.length === 0) {
    elements.cloudProvidersContainer.innerHTML = `
      <p style="color: var(--hud-dim); font-family: var(--font-mono);">
        // No se detectaron clientes de OneDrive, Google Drive o Dropbox instalados. Puedes configurar una carpeta personalizada abajo.
      </p>
    `;
    elements.statCloudStatus.textContent = "NO DETECTADO";
    return;
  }

  elements.statCloudStatus.textContent = "ENLACE DISPONIBLE";

  cloudProviders.forEach(p => {
    const isSelected = (schedulerConfig.cloud_provider === p.id);
    const item = document.createElement("div");
    item.className = `cloud-provider-item ${isSelected ? 'active' : ''}`;
    item.dataset.providerId = p.id;
    item.innerHTML = `
      <div class="provider-info">
        <div class="provider-title">${p.name}</div>
        <div class="provider-path">${p.sync_folder}</div>
      </div>
      <span class="badge-sector badge-savedgames">${isSelected ? 'ACTIVO' : 'CONECTADO'}</span>
    `;

    item.addEventListener("click", () => {
      document.querySelectorAll(".cloud-provider-item").forEach(c => c.classList.remove("active"));
      item.classList.add("active");
      schedulerConfig.cloud_provider = p.id;
      schedulerConfig.cloud_sync_enabled = true;
      elements.statCloudStatus.textContent = p.name.toUpperCase();
      showToast(`Proveedor seleccionado: ${p.name}`);
    });

    elements.cloudProvidersContainer.appendChild(item);
  });

  if (schedulerConfig.custom_cloud_path) {
    elements.customCloudInput.value = schedulerConfig.custom_cloud_path;
  }
}

function renderSchedulerConfig() {
  elements.schedulerToggle.checked = !!schedulerConfig.enabled;
  elements.schedulerLastRun.textContent = schedulerConfig.last_auto_backup || "Sin ejecuciones previas";
  elements.schedulerStatusText.textContent = schedulerConfig.last_backup_status || (schedulerConfig.enabled ? "Activo en segundo plano" : "Desactivado");

  // Interval chips
  const interval = schedulerConfig.interval_hours || 6;
  document.querySelectorAll(".interval-chip").forEach(c => {
    c.classList.toggle("active", parseInt(c.dataset.hours) === interval);
  });
}

// -------------------------------------------------------------
// EVENT LISTENERS & INITS
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  // Navigation Tabs
  elements.navTabs.forEach(tab => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });

  // Search & Filters
  elements.searchInput.addEventListener("input", applyFilters);
  elements.searchClear.addEventListener("click", () => {
    elements.searchInput.value = "";
    applyFilters();
    elements.searchInput.focus();
  });

  elements.filterChips.addEventListener("click", (e) => {
    const chip = e.target.closest(".hud-chip");
    if (!chip) return;
    document.querySelectorAll(".hud-chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    currentFilter = chip.dataset.filter;
    applyFilters();
  });

  // Selection
  elements.btnSelectAll.addEventListener("click", () => {
    filteredGames.forEach(g => selectedGamePaths.add(g.path));
    renderGames();
    showToast(`${selectedGamePaths.size} bloques marcados`);
  });

  elements.btnDeselectAll.addEventListener("click", () => {
    selectedGamePaths.clear();
    renderGames();
    showToast("Selección restablecida");
  });

  // Master Backup Trigger
  elements.btnMasterBackup.addEventListener("click", async () => {
    const selectedGames = allGames.filter(g => selectedGamePaths.has(g.path));
    if (selectedGames.length === 0) return;

    elements.btnMasterBackup.disabled = true;
    elements.btnMasterBackup.textContent = "COMPRIMIENDO MATRIZ...";

    try {
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.create_master_backup(selectedGames, "Formateo_PC");
        if (res.success) {
          showToast(`PAQUETE MAESTRO CONSOLIDADO: ${res.total_games} BLOQUES GUARDADOS EN ${res.filename}`, 5000);
          refreshBackupsCount();
        } else {
          showToast("ERROR EN LA CONSOLIDACIÓN: " + (res.error || "Desconocido"));
        }
      }
    } catch (err) {
      showToast("Error de empaquetado: " + err);
    } finally {
      elements.btnMasterBackup.disabled = false;
      elements.btnMasterBackup.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
        CREAR PAQUETE MAESTRO (.ZIP)
      `;
    }
  });

  // Master Restore Trigger
  elements.btnRestoreMaster.addEventListener("click", async () => {
    if (!window.pywebview || !window.pywebview.api) return;
    const zipPath = await window.pywebview.api.choose_master_backup_file();
    if (!zipPath) return;

    showToast("DESFRAGMENTANDO Y RESTAURANDO MATRIZ DE MEMORIA...");
    try {
      const res = await window.pywebview.api.restore_master_backup(zipPath);
      if (res.success) {
        elements.restoreSummaryText.textContent = `Se restauraron exitosamente ${res.total_restored} bloques de memoria a sus ubicaciones de memoria en este host.`;
        elements.restoreGamesList.innerHTML = "";
        const fragment = document.createDocumentFragment();
        (res.games || []).forEach(g => {
          const item = document.createElement("div");
          item.className = "backup-item";
          item.innerHTML = `
            <div class="backup-info">
              <div class="backup-name">${g.name}</div>
              <div class="backup-meta">
                <span>DESTINO: <code>${g.destination}</code></span>
                <span>[${g.files_restored} ARCHIVOS]</span>
              </div>
            </div>
            <button class="hud-btn hud-btn-outline btn-open-target" data-path="${g.destination}" style="padding: 4px 8px; font-size: 10px;">VER</button>
          `;
          fragment.appendChild(item);
        });
        elements.restoreGamesList.appendChild(fragment);
        elements.restoreResultModal.classList.remove("hidden");
        triggerScan();
      } else {
        showToast("Error de restauración: " + (res.error || "Archivo no compatible"));
      }
    } catch (err) {
      showToast("Fallo crítico en restauración: " + err);
    }
  });

  // Cloud & Scheduler Actions
  elements.btnBrowseCloudFolder.addEventListener("click", async () => {
    if (window.pywebview && window.pywebview.api) {
      const p = await window.pywebview.api.choose_custom_cloud_folder();
      if (p) {
        elements.customCloudInput.value = p;
        schedulerConfig.custom_cloud_path = p;
        schedulerConfig.cloud_provider = "custom";
        schedulerConfig.cloud_sync_enabled = true;
        showToast("Carpeta personalizada vinculada");
      }
    }
  });

  elements.btnSyncCloudNow.addEventListener("click", async () => {
    if (!window.pywebview || !window.pywebview.api) return;
    const providerId = schedulerConfig.cloud_provider || "onedrive";
    const customP = elements.customCloudInput.value;
    showToast("Sincronizando respaldos hacia la nube...");

    const res = await window.pywebview.api.sync_to_cloud(providerId, customP);
    if (res.success) {
      showToast(`// Sincronización en la nube exitosa (${res.synced_count} archivos actualizados)`, 5000);
    } else {
      showToast(`// Error en sincronización: ${res.error}`);
    }
  });

  elements.intervalChips.addEventListener("click", (e) => {
    const chip = e.target.closest(".interval-chip");
    if (!chip) return;
    document.querySelectorAll(".interval-chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    schedulerConfig.interval_hours = parseInt(chip.dataset.hours);
  });

  elements.btnSaveScheduler.addEventListener("click", async () => {
    if (!window.pywebview || !window.pywebview.api) return;
    schedulerConfig.enabled = elements.schedulerToggle.checked;
    const res = await window.pywebview.api.save_scheduler_config(schedulerConfig);
    if (res.success) {
      showToast("Configuración del programador guardada con éxito");
      loadCloudAndScheduler();
    }
  });

  elements.btnTriggerAutoNow.addEventListener("click", async () => {
    if (!window.pywebview || !window.pywebview.api) return;
    showToast("Ejecutando ciclo de auto-backup manual...");
    const res = await window.pywebview.api.trigger_auto_backup_now();
    if (res.success) {
      showToast(res.message, 4500);
      loadCloudAndScheduler();
      refreshBackupsCount();
    } else {
      showToast("Error: " + (res.error || "Fallo en auto-backup"));
    }
  });

  // Global Grid clicks (checkboxes, copy, actions)
  elements.gamesGrid.addEventListener("click", async (e) => {
    if (e.target.classList.contains("hud-checkbox")) {
      const p = e.target.dataset.path;
      if (e.target.checked) selectedGamePaths.add(p);
      else selectedGamePaths.delete(p);
      const card = e.target.closest(".memory-card");
      if (card) card.classList.toggle("selected", e.target.checked);
      updateSelectionBar();
      return;
    }

    const copyBtn = e.target.closest(".btn-copy-address");
    if (copyBtn) {
      const p = copyBtn.dataset.path;
      if (p) {
        navigator.clipboard.writeText(p);
        showToast("Dirección copiada al portapapeles");
      }
      return;
    }

    const actionBtn = e.target.closest(".btn-card-action");
    if (!actionBtn) return;
    const action = actionBtn.dataset.action;
    const path = actionBtn.dataset.path;
    const name = actionBtn.dataset.name;

    if (action === "open") {
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.open_explorer(path);
      }
    } else if (action === "history") {
      openVersionHistory(name, path);
    } else if (action === "backup") {
      actionBtn.disabled = true;
      actionBtn.textContent = "COMPRIMIENDO...";
      try {
        if (window.pywebview && window.pywebview.api) {
          const res = await window.pywebview.api.backup_game(path, name);
          if (res.success) {
            showToast(`Punto de guardado para "${name}" creado con éxito`);
            refreshBackupsCount();
            await refreshVersionCounts();
          } else {
            showToast(`Error: ${res.error || 'No se pudo crear el backup'}`);
          }
        }
      } catch (err) {
        showToast("Error al respaldar partida: " + err);
      } finally {
        actionBtn.disabled = false;
        actionBtn.innerHTML = `
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
          RESPALDO .ZIP
        `;
      }
    }
  });

  // Modal Historial de Versiones
  elements.versionModalClose.addEventListener("click", () => elements.versionHistoryModal.classList.add("hidden"));
  elements.btnVersionModalClose.addEventListener("click", () => elements.versionHistoryModal.classList.add("hidden"));
  elements.btnVersionModalOpenFolder.addEventListener("click", async () => {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.open_backups_folder();
    }
  });

  elements.btnCreateVersionSnapshot.addEventListener("click", handleCreateVersionSnapshot);
  elements.inputVersionNote.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleCreateVersionSnapshot();
  });

  elements.versionTimelineList.addEventListener("click", async (e) => {
    const revertBtn = e.target.closest(".btn-revert-version");
    if (revertBtn) {
      const p = revertBtn.dataset.path;
      const d = revertBtn.dataset.date;
      await handleRevertToVersion(p, d);
      return;
    }

    const openBtn = e.target.closest(".btn-open-version");
    if (openBtn) {
      const p = openBtn.dataset.path;
      if (window.pywebview && window.pywebview.api) await window.pywebview.api.open_explorer(p);
      return;
    }

    const deleteBtn = e.target.closest(".btn-delete-version");
    if (deleteBtn) {
      const p = deleteBtn.dataset.path;
      await handleDeleteVersion(p);
      return;
    }
  });

  // Modals Backups
  elements.btnOpenBackupsFolder.addEventListener("click", async () => {
    await refreshBackupsCount();
    renderBackupsModal();
    elements.backupsModal.classList.remove("hidden");
  });

  elements.modalClose.addEventListener("click", () => elements.backupsModal.classList.add("hidden"));
  elements.btnModalClose.addEventListener("click", () => elements.backupsModal.classList.add("hidden"));
  elements.restoreModalClose.addEventListener("click", () => elements.restoreResultModal.classList.add("hidden"));
  elements.btnRestoreModalClose.addEventListener("click", () => elements.restoreResultModal.classList.add("hidden"));

  if (elements.backupsFilterInput) {
    elements.backupsFilterInput.addEventListener("input", renderBackupsModal);
  }

  elements.btnModalOpenFolder.addEventListener("click", async () => {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.open_backups_folder();
    }
  });

  elements.modalBackupsList.addEventListener("click", async (e) => {
    const openBtn = e.target.closest(".btn-open-item");
    if (openBtn) {
      const p = openBtn.dataset.path;
      if (window.pywebview && window.pywebview.api) await window.pywebview.api.open_explorer(p);
      return;
    }

    const restoreBtn = e.target.closest(".btn-restore-item");
    if (restoreBtn) {
      const p = restoreBtn.dataset.path;
      elements.backupsModal.classList.add("hidden");
      await handleRestoreMasterBackup(p);
      return;
    }

    const revertBtn = e.target.closest(".btn-revert-from-modal");
    if (revertBtn) {
      const p = revertBtn.dataset.path;
      const target = revertBtn.dataset.target || "";
      const d = revertBtn.dataset.date || "fecha previa";
      const n = revertBtn.dataset.name || "la partida";
      if (confirm(`¿Deseas restaurar "${n}" al estado del ${d}?\n\n• Se creará una copia de seguridad automática del estado presente antes de continuar.`)) {
        showToast("REVIRTIENDO PARTIDA...");
        if (window.pywebview && window.pywebview.api) {
          const res = await window.pywebview.api.revert_to_version(p, target);
          if (res.success) {
            showToast(`Partida revertida exitosamente. Respaldo previo resguardado.`);
            await refreshBackupsCount();
            await refreshVersionCounts();
            renderBackupsModal();
          } else {
            showToast("Error al revertir: " + (res.error || ""));
          }
        }
      }
      return;
    }

    const deleteBtn = e.target.closest(".btn-delete-backup-item");
    if (deleteBtn) {
      const p = deleteBtn.dataset.path;
      await handleDeleteVersion(p);
      return;
    }
  });

  elements.restoreGamesList.addEventListener("click", async (e) => {
    const openBtn = e.target.closest(".btn-open-target");
    if (openBtn) {
      const p = openBtn.dataset.path;
      if (window.pywebview && window.pywebview.api) await window.pywebview.api.open_explorer(p);
    }
  });

  // Trigger scan button
  elements.btnScan.addEventListener("click", triggerScan);

  // Init
  window.addEventListener("pywebviewready", () => {
    triggerScan();
  });

  setTimeout(() => {
    if (allGames.length === 0 && window.pywebview && window.pywebview.api) {
      triggerScan();
    }
  }, 1000);
});

// -------------------------------------------------------------
// CONTROLADOR DEL HISTORIAL DE VERSIONES
// -------------------------------------------------------------
async function openVersionHistory(gameName, gamePath) {
  currentGameForHistory = { name: gameName, path: gamePath };
  elements.versionModalGameTitle.textContent = `HISTORIAL DE VERSIONES // ${gameName.toUpperCase()}`;
  elements.versionModalGamePath.textContent = gamePath;
  elements.inputVersionNote.value = "";

  // Mostrar portada oficial en el modal si está disponible
  const gameObj = allGames.find(g => g.path === gamePath || g.name.toLowerCase() === gameName.toLowerCase());
  if (gameObj && elements.versionModalHero && elements.versionModalHeroImg) {
    const heroSrc = gameObj.image_url || gameObj.capsule_url || gameObj.procedural_banner;
    if (heroSrc) {
      elements.versionModalHeroImg.src = heroSrc;
      elements.versionModalHero.classList.remove("hidden");
    } else {
      elements.versionModalHero.classList.add("hidden");
    }
  } else if (elements.versionModalHero) {
    elements.versionModalHero.classList.add("hidden");
  }

  elements.versionHistoryModal.classList.remove("hidden");
  await loadGameVersions(gameName, gamePath);
}

async function loadGameVersions(gameName, gamePath) {
  elements.versionTimelineList.innerHTML = "";
  elements.versionEmptyState.classList.add("hidden");

  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.get_game_versions) {
    return;
  }

  try {
    currentGameVersions = await window.pywebview.api.get_game_versions(gameName, gamePath) || [];
  } catch (err) {
    console.error("Error al obtener versiones del juego:", err);
    currentGameVersions = [];
  }

  const count = currentGameVersions.length;
  elements.versionCountLabel.textContent = `${count} ${count === 1 ? 'VERSIÓN REGISTRADA' : 'VERSIONES REGISTRADAS'}`;

  if (count === 0) {
    elements.versionEmptyState.classList.remove("hidden");
    return;
  }

  const fragment = document.createDocumentFragment();
  currentGameVersions.forEach(v => {
    const item = document.createElement("div");
    item.className = `version-item ${v.is_safety ? 'is-safety' : ''}`;
    item.dataset.path = v.path;
    item.innerHTML = `
      <div class="version-item-header">
        <div class="version-meta-left">
          <div class="version-timestamp-title">
            <span>${v.date}</span>
            ${v.relative_time ? `<span class="version-rel-time">${v.relative_time}</span>` : ''}
          </div>
          ${v.note ? `<div class="version-note-text">"${v.note}"</div>` : ''}
        </div>
        <div class="version-badges-row">
          ${v.is_safety ? '<span class="badge-safety">SEGURIDAD PREVIA</span>' : ''}
        </div>
      </div>
      <div class="version-stats-row">
        <span>TAMAÑO: <strong>${v.size_str}</strong></span>
        ${v.file_count ? `<span>ARCHIVOS: <strong>${v.file_count}</strong></span>` : ''}
        <span>ARCHIVO: <strong>${v.filename}</strong></span>
      </div>
      <div class="version-actions-row">
        <button class="btn-revert-version" data-path="${v.path}" data-date="${v.date}">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
          REVERTIR A ESTA VERSIÓN
        </button>
        <button class="hud-btn hud-btn-outline btn-open-version" data-path="${v.path}" style="padding: 5px 9px; font-size: 10.5px;">
          EXPLORAR
        </button>
        <button class="btn-delete-version" data-path="${v.path}" title="Eliminar este punto de guardado">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          ELIMINAR
        </button>
      </div>
    `;
    fragment.appendChild(item);
  });

  elements.versionTimelineList.appendChild(fragment);
}

async function handleCreateVersionSnapshot() {
  if (!currentGameForHistory) return;
  const note = elements.inputVersionNote.value.trim();

  elements.btnCreateVersionSnapshot.disabled = true;
  elements.btnCreateVersionSnapshot.textContent = "GUARDANDO ESTADO...";

  try {
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.backup_game(
        currentGameForHistory.path,
        currentGameForHistory.name,
        note
      );
      if (res.success) {
        showToast(`Punto de guardado para "${currentGameForHistory.name}" registrado con éxito`);
        elements.inputVersionNote.value = "";
        await loadGameVersions(currentGameForHistory.name, currentGameForHistory.path);
        await refreshVersionCounts();
        refreshBackupsCount();
      } else {
        showToast("Error al guardar versión: " + (res.error || "Desconocido"));
      }
    }
  } catch (err) {
    showToast("Error: " + err);
  } finally {
    elements.btnCreateVersionSnapshot.disabled = false;
    elements.btnCreateVersionSnapshot.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
      <span>GUARDAR VERSIÓN ACTUAL</span>
    `;
  }
}

async function handleRevertToVersion(zipPath, versionDate) {
  if (!currentGameForHistory) return;
  const confirmMsg = `¿Confirmas revertir la partida de "${currentGameForHistory.name}" al estado del ${versionDate}?\n\n` +
    `• Los archivos actuales del juego serán sustituidos con esta versión.\n` +
    `• Se creará automáticamente un respaldo de seguridad del estado presente antes de continuar.`;

  if (!confirm(confirmMsg)) return;

  showToast(`REVIRTIENDO PARTIDA A VERSIÓN ANTERIOR...`);

  try {
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.revert_to_version(zipPath, currentGameForHistory.path);
      if (res.success) {
        showToast(`PARTIDA REVERTIDA EXITOSAMENTE. Respaldo de seguridad previo resguardado.`, 5000);
        await loadGameVersions(currentGameForHistory.name, currentGameForHistory.path);
        await refreshVersionCounts();
        refreshBackupsCount();
      } else {
        showToast("Fallo al revertir partida: " + (res.error || "Error desconocido"));
      }
    }
  } catch (err) {
    showToast("Error crítico en reversión: " + err);
  }
}

async function handleDeleteVersion(zipPath) {
  if (!confirm("¿Deseas eliminar permanentemente este archivo de respaldo?")) return;

  try {
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.delete_backup(zipPath);
      if (res.success) {
        showToast("Archivo de respaldo eliminado con éxito");
        if (currentGameForHistory) {
          await loadGameVersions(currentGameForHistory.name, currentGameForHistory.path);
        }
        await refreshVersionCounts();
        refreshBackupsCount();
        renderBackupsModal();
      } else {
        showToast("No se pudo eliminar el respaldo: " + (res.error || ""));
      }
    }
  } catch (err) {
    showToast("Error: " + err);
  }
}

async function refreshBackupsCount() {
  if (window.pywebview && window.pywebview.api) {
    try {
      backupsList = await window.pywebview.api.get_backups();
      elements.backupsCount.textContent = backupsList.length;
    } catch (e) {
      console.error(e);
    }
  }
}

function renderBackupsModal() {
  elements.modalBackupsList.innerHTML = "";
  if (backupsList.length === 0) {
    elements.modalBackupsList.innerHTML = `<p style="color: var(--hud-dim); text-align: center; padding: 24px 0; font-family: var(--font-mono);">// NO HAY REGISTROS DE RESPALDO DISPONIBLES.</p>`;
    return;
  }

  const query = (elements.backupsFilterInput ? elements.backupsFilterInput.value.toLowerCase().trim() : "");
  const filtered = backupsList.filter(b => {
    if (!query) return true;
    const nameMatch = (b.game_name || "").toLowerCase().includes(query);
    const fileMatch = (b.filename || "").toLowerCase().includes(query);
    const noteMatch = (b.note || "").toLowerCase().includes(query);
    return nameMatch || fileMatch || noteMatch;
  });

  if (filtered.length === 0) {
    elements.modalBackupsList.innerHTML = `<p style="color: var(--hud-dim); text-align: center; padding: 24px 0; font-family: var(--font-mono);">// NO HAY RESPALDOS QUE COINCIDAN CON EL FILTRO.</p>`;
    return;
  }

  const fragment = document.createDocumentFragment();
  filtered.forEach(b => {
    const item = document.createElement("div");
    item.className = "backup-item";
    item.innerHTML = `
      <div class="backup-info">
        <div class="backup-name" title="${b.filename}">
          ${b.game_name ? `<span style="color: #fff; font-weight: 700;">${b.game_name}</span> - ` : ''}${b.filename}
          ${b.is_master ? '<span class="badge-master">PAQUETE MAESTRO</span>' : ''}
          ${b.is_safety ? '<span class="badge-safety">SEGURIDAD PREVIA</span>' : ''}
        </div>
        ${b.note ? `<div style="font-family: var(--font-hud); font-size: 11px; color: var(--animus-cyan); margin: 2px 0;">"${b.note}"</div>` : ''}
        <div class="backup-meta">
          <span>FECHA: ${b.date}</span>
          <span>PESO: ${b.size_str}</span>
        </div>
      </div>
      <div style="display: flex; gap: 6px; align-items: center;">
        ${b.is_master ? `
          <button class="hud-btn hud-btn-cyan btn-restore-item" data-path="${b.path}" style="padding: 5px 10px; font-size: 10px;">
            RESTAURAR MATRIZ
          </button>
        ` : `
          <button class="hud-btn hud-btn-cyan btn-revert-from-modal" data-path="${b.path}" data-target="${b.source_path || ''}" data-date="${b.date}" data-name="${b.game_name || ''}" style="padding: 5px 10px; font-size: 10px;">
            REVERTIR
          </button>
        `}
        <button class="hud-btn hud-btn-outline btn-open-item" data-path="${b.path}" style="padding: 5px 10px; font-size: 10px;">
          ABRIR
        </button>
        <button class="btn-delete-version btn-delete-backup-item" data-path="${b.path}" title="Eliminar archivo" style="padding: 4px 7px;">
          &times;
        </button>
      </div>
    `;
    fragment.appendChild(item);
  });
  elements.modalBackupsList.appendChild(fragment);
}
