/**
 * King-Phisher Extension - Popup Script
 */

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('http://localhost:5000/api/scan-stats');
        const data = await response.json();

        if (data.success) {
            document.getElementById('scansToday').textContent = data.stats.total_scans || 0;
            document.getElementById('phishingDetected').textContent = data.stats.phishing_count || 0;
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Load settings
chrome.storage.sync.get(['autoScan'], (result) => {
    document.getElementById('autoScanToggle').checked = result.autoScan || false;
});

// Save auto-scan setting
document.getElementById('autoScanToggle').addEventListener('change', (e) => {
    const enabled = e.target.checked;
    chrome.storage.sync.set({ autoScan: enabled });
    localStorage.setItem('kingphisher_autoscan', enabled);
});

// Load stats on popup open
loadStats();
