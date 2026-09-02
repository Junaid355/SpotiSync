/**
 * Spotify & Spicetify Auto-Setup Suite - Frontend Logic
 */

// State
let isBusy = false;

// DOM Elements
const badgeElement = document.getElementById('system-badge');
const badgeText = document.getElementById('badge-text');
const btnRefresh = document.getElementById('btn-refresh');

const spotifyPathText = document.getElementById('spotify-path-text');
const spotifyStatusPill = document.getElementById('spotify-status-pill');
const spotifyRunningText = document.getElementById('spotify-running-text');
const spotifyEditionText = document.getElementById('spotify-edition-text');

const spicetifyVersionText = document.getElementById('spicetify-version-text');
const spicetifyStatusPill = document.getElementById('spicetify-status-pill');
const marketplaceStatusText = document.getElementById('marketplace-status-text');
const patchStatusText = document.getElementById('patch-status-text');

const startupToggle = document.getElementById('startup-toggle');
const btnAutoSetup = document.getElementById('btn-auto-setup');
const btnLaunchSpotify = document.getElementById('btn-launch-spotify');
const btnApplySpicetify = document.getElementById('btn-apply-spicetify');
const btnInstallMarketplace = document.getElementById('btn-install-marketplace');
const btnKillSpotify = document.getElementById('btn-kill-spotify');

const logTerminal = document.getElementById('log-terminal');
const btnClearLogs = document.getElementById('btn-clear-logs');
const footerTime = document.getElementById('footer-time');

// Logger function
function appendLog(message, level = 'info') {
    const line = document.createElement('div');
    line.className = `log-line log-${level}`;
    const timestamp = new Date().toLocaleTimeString();
    line.textContent = `[${timestamp}] ${message}`;
    logTerminal.appendChild(line);
    logTerminal.scrollTop = logTerminal.scrollHeight;
}

// Global hooks for Python backend logs & events
window.receiveBackendLog = function(message, level) {
    appendLog(message, level || 'info');
};

window.receiveBackendStatus = function(statusJson) {
    const status = typeof statusJson === 'string' ? JSON.parse(statusJson) : statusJson;
    renderStatus(status);
};

window.onActionCompleted = function() {
    setBusyState(false);
    appendLog('Action execution completed.', 'success');
};

// Render Status to UI
function renderStatus(status) {
    if (!status) return;

    const spotify = status.spotify || {};
    const spicetify = status.spicetify || {};
    const system = status.system || {};

    // Spotify Card
    if (spotify.installed) {
        spotifyPathText.textContent = spotify.path || 'Installed';
        spotifyStatusPill.className = 'pill pill-ready';
        spotifyStatusPill.textContent = 'Installed';
        spotifyRunningText.textContent = spotify.running ? '🟢 Active & Running' : '⚪ Stopped';
        spotifyEditionText.textContent = spotify.is_ms_store ? '⚠️ Microsoft Store (Unsupported)' : 'Win32 Standalone (Supported)';
    } else {
        spotifyPathText.textContent = 'Not Installed';
        spotifyStatusPill.className = 'pill pill-missing';
        spotifyStatusPill.textContent = 'Missing';
        spotifyRunningText.textContent = 'No';
        spotifyEditionText.textContent = '-';
    }

    // Spicetify Card
    if (spicetify.installed) {
        spicetifyVersionText.textContent = `v${spicetify.version || 'Ready'}`;
        spicetifyStatusPill.className = 'pill pill-ready';
        spicetifyStatusPill.textContent = 'Installed';
    } else {
        spicetifyVersionText.textContent = 'Not Installed';
        spicetifyStatusPill.className = 'pill pill-missing';
        spicetifyStatusPill.textContent = 'Missing';
    }

    marketplaceStatusText.textContent = spicetify.marketplace_installed ? '✅ Active / Ready' : '❌ Not Installed';
    patchStatusText.textContent = spicetify.applied ? '✅ Patches Applied' : '⚠️ Pending / Unpatched';

    // System Badge
    if (spotify.installed && spicetify.installed && spicetify.marketplace_installed && spicetify.applied) {
        badgeElement.className = 'badge badge-success';
        badgeText.textContent = 'All Systems Ready';
    } else if (!spotify.installed || !spicetify.installed) {
        badgeElement.className = 'badge badge-danger';
        badgeText.textContent = 'Setup Required';
    } else {
        badgeElement.className = 'badge badge-warning';
        badgeText.textContent = 'Patch Pending';
    }

    // Startup Toggle
    startupToggle.checked = !!system.startup_enabled;

    footerTime.textContent = `Last Checked: ${new Date().toLocaleTimeString()}`;
}

// Wait for Python API to be available
function waitForApi() {
    return new Promise((resolve) => {
        if (window.pywebview && window.pywebview.api) {
            return resolve(window.pywebview.api);
        }
        let attempts = 0;
        const interval = setInterval(() => {
            attempts++;
            if (window.pywebview && window.pywebview.api) {
                clearInterval(interval);
                resolve(window.pywebview.api);
            } else if (attempts > 50) { // 5 seconds max
                clearInterval(interval);
                resolve(null);
            }
        }, 100);
    });
}

// Bridge API helper
async function callApi(method, ...args) {
    const api = await waitForApi();
    if (api && typeof api[method] === 'function') {
        try {
            return await api[method](...args);
        } catch (err) {
            appendLog(`API Error (${method}): ${err}`, 'error');
            setBusyState(false);
            return null;
        }
    } else {
        appendLog(`Backend API not connected yet for ${method}. Please wait a moment...`, 'warning');
        setBusyState(false);
        return null;
    }
}

// Refresh status
async function refreshStatus() {
    appendLog('Checking system diagnostics...', 'info');
    const status = await callApi('get_status');
    if (status) {
        renderStatus(status);
        appendLog('Diagnostics updated.', 'success');
    }
}

// Set busy UI state
function setBusyState(busy, btnElement = null) {
    isBusy = busy;
    if (btnElement) {
        if (busy) {
            btnElement.classList.add('is-loading');
        } else {
            btnElement.classList.remove('is-loading');
        }
    } else {
        btnAutoSetup.classList.remove('is-loading');
    }

    const allButtons = document.querySelectorAll('.action-btn, .btn');
    allButtons.forEach(btn => {
        btn.disabled = busy;
        btn.style.opacity = busy ? '0.6' : '1';
    });
}

// Action Handlers
btnAutoSetup.addEventListener('click', async () => {
    if (isBusy) return;
    setBusyState(true, btnAutoSetup);
    appendLog('Starting 1-Click Automated Setup...', 'info');
    await callApi('auto_setup_all');
});

btnLaunchSpotify.addEventListener('click', async () => {
    if (isBusy) return;
    appendLog('Launching Spotify...', 'info');
    await callApi('launch_spotify');
});

btnApplySpicetify.addEventListener('click', async () => {
    if (isBusy) return;
    setBusyState(true);
    appendLog('Applying Spicetify patch...', 'info');
    await callApi('apply_spicetify');
});

btnInstallMarketplace.addEventListener('click', async () => {
    if (isBusy) return;
    setBusyState(true);
    appendLog('Setting up Spicetify Marketplace...', 'info');
    await callApi('install_marketplace');
});

btnKillSpotify.addEventListener('click', async () => {
    if (isBusy) return;
    appendLog('Stopping Spotify processes...', 'info');
    await callApi('kill_spotify');
});

startupToggle.addEventListener('change', async (e) => {
    const isChecked = e.target.checked;
    appendLog(`Setting Windows Startup Auto-Check to ${isChecked ? 'Enabled' : 'Disabled'}...`, 'info');
    await callApi('set_startup_enabled', isChecked);
});

btnRefresh.addEventListener('click', refreshStatus);

btnClearLogs.addEventListener('click', () => {
    logTerminal.innerHTML = '<div class="log-line log-info">[System] Logs cleared.</div>';
});

// Initialization
window.addEventListener('pywebviewready', () => {
    appendLog('PyWebView bridge connected.', 'success');
    refreshStatus();
});

// Initial auto-refresh
setTimeout(refreshStatus, 300);
