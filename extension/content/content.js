// Constants
const MAX_EMAIL_LENGTH = 50000;
const API_BASE = 'http://localhost:8000';

// Utility: Debounce to prevent over-scanning
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Helper: Get Auth Token
async function getAuthToken() {
    const result = await chrome.storage.local.get(['auth_token']);
    return result.auth_token;
}

// 🌐 1. Real-time URL Scanner (Runs on every page load)
(async () => {
    const url = window.location.href;
    if (url.startsWith('chrome://') || url.includes('localhost:8000')) return;

    try {
        console.log('King Phisher AI: Auto-scanning URL...');
        const token = await getAuthToken();
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`${API_BASE}/scan-url`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ url })
        });

        const data = await response.json();
        if (data.is_phishing) {
            console.warn('King Phisher AI: PHISHING DETECTED!');
            injectWarning(data.explanation);
        }
    } catch (error) {
        console.error('King Phisher AI: URL scan failed.', error);
    }
})();

// 📧 2. Gmail Scanner
if (window.location.hostname === 'mail.google.com') {
    console.log('King Phisher AI: Gmail detected. Initializing Smart-Scanner...');
    
    const scanEmails = debounce(() => {
        // We look for common Gmail email body containers
        const selectors = ['.a3s.aiL', '.ii.gt', '.adP', '.adO'];
        let found = false;

        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (!element.dataset.scanned && element.innerText.trim().length > 10) {
                    console.log('King Phisher AI: New email body found. Scanning...');
                    scanEmailContent(element);
                    found = true;
                }
            });
        });
    }, 1000);

    // Initial scan in case email is already open
    setTimeout(scanEmails, 2000);

    // Watch for new emails being opened
    const observer = new MutationObserver(scanEmails);
    observer.observe(document.body, { childList: true, subtree: true });
}

async function scanEmailContent(element) {
    element.dataset.scanned = 'true';
    let text = element.innerText;

    if (text.length > MAX_EMAIL_LENGTH) {
        text = text.substring(0, MAX_EMAIL_LENGTH);
    }

    try {
        const token = await getAuthToken();
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`${API_BASE}/scan-email`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ text })
        });

        const data = await response.json();
        if (data.is_phishing) {
            console.warn('King Phisher AI: Phishing patterns detected in email!');
            highlightSuspiciousEmail(element, data.explanation);
        } else {
            console.log('King Phisher AI: Email scan complete. Result: Safe.');
        }
    } catch (error) {
        console.error('King Phisher AI: Email scan failed.', error);
    }
}

// UI Injectors
function injectWarning(reason) {
    if (document.getElementById('kp-phishing-overlay')) return;

    const overlay = document.createElement('div');
    overlay.id = 'kp-phishing-overlay';
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(127, 29, 29, 0.98); color: white; z-index: 2147483647;
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; font-family: sans-serif; text-align: center; padding: 40px;
    `;

    overlay.innerHTML = `
        <h1 style="font-size: 3rem; margin-bottom: 20px;">⚠️ PHISHING ALERT</h1>
        <p style="font-size: 1.5rem; margin-bottom: 30px;">This website has been flagged as suspicious by King Phisher AI.</p>
        <div style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; margin-bottom: 30px; max-width: 600px;">
            <strong>Reason:</strong> ${reason}
        </div>
        <div style="display: flex; gap: 20px;">
            <button id="kp-back" style="padding: 15px 30px; font-size: 1.2rem; cursor: pointer; border: none; border-radius: 5px; background: white; color: #7f1d1d; font-weight: bold;">Go Back to Safety</button>
            <button id="kp-ignore" style="padding: 15px 30px; font-size: 1.2rem; cursor: pointer; border: 1px solid white; border-radius: 5px; background: transparent; color: white;">I Understand the Risk</button>
        </div>
    `;

    document.body.appendChild(overlay);
    document.getElementById('kp-back').onclick = () => history.back();
    document.getElementById('kp-ignore').onclick = () => overlay.remove();
}

function highlightSuspiciousEmail(element, reason) {
    element.style.border = '3px solid #ef4444';
    element.style.backgroundColor = 'rgba(239, 68, 68, 0.05)';
    element.style.padding = '15px';
    element.style.borderRadius = '12px';
    
    const warning = document.createElement('div');
    warning.style.cssText = `
        background: #ef4444; color: white; padding: 15px; margin-bottom: 20px;
        border-radius: 8px; font-weight: bold; font-size: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #7f1d1d;
    `;
    warning.innerHTML = `⚠️ King Phisher AI: PHISHING DETECTED<br>
                        <span style="font-weight: normal; font-size: 0.85rem; opacity: 0.9;">Reason: ${reason}</span>`;
    element.prepend(warning);
}
