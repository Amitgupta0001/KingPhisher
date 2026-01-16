/**
 * King-Phisher Chrome Extension - Content Script
 * Integrates with Gmail to provide real-time phishing detection
 */

// Configuration
const API_BASE_URL = 'http://localhost:5000';
let isProcessing = false;

// Gmail selectors
const SELECTORS = {
    emailBody: '.a3s.aiL',
    emailSubject: '.hP',
    emailFrom: '.gD',
    emailLinks: '.a3s.aiL a',
    toolbar: '.iH.bzn'
};

/**
 * Initialize extension when Gmail loads
 */
function init() {
    console.log('🛡️ King-Phisher: Initializing...');

    // Add scan button to Gmail toolbar
    addScanButton();

    // Monitor for new emails
    observeEmailChanges();

    // Auto-scan on email open (optional)
    const autoScan = localStorage.getItem('kingphisher_autoscan') === 'true';
    if (autoScan) {
        scanCurrentEmail();
    }
}

/**
 * Add scan button to Gmail toolbar
 */
function addScanButton() {
    const toolbar = document.querySelector(SELECTORS.toolbar);
    if (!toolbar || document.getElementById('kingphisher-scan-btn')) return;

    const button = document.createElement('div');
    button.id = 'kingphisher-scan-btn';
    button.className = 'T-I J-J5-Ji nX T-I-ax7 T-I-Js-Gs mA';
    button.innerHTML = `
    <div class="asa">
      <span class="kingphisher-icon">🛡️</span>
      <span class="kingphisher-text">Scan for Phishing</span>
    </div>
  `;
    button.title = 'Scan this email with King-Phisher';
    button.style.cssText = 'margin-left: 8px; cursor: pointer;';

    button.addEventListener('click', scanCurrentEmail);

    toolbar.appendChild(button);
    console.log('✅ Scan button added');
}

/**
 * Scan current email for phishing
 */
async function scanCurrentEmail() {
    if (isProcessing) return;
    isProcessing = true;

    try {
        // Extract email data
        const emailData = extractEmailData();
        if (!emailData) {
            showNotification('No email selected', 'warning');
            return;
        }

        // Show loading state
        updateScanButton('scanning');

        // Extract features from email
        const features = await extractFeatures(emailData.body);

        // Send to API for scanning
        const result = await scanEmail(features, emailData);

        // Display result
        displayResult(result, emailData);

    } catch (error) {
        console.error('Scan error:', error);
        showNotification('Scan failed: ' + error.message, 'error');
    } finally {
        isProcessing = false;
        updateScanButton('idle');
    }
}

/**
 * Extract email data from Gmail DOM
 */
function extractEmailData() {
    const subject = document.querySelector(SELECTORS.emailSubject)?.textContent || '';
    const from = document.querySelector(SELECTORS.emailFrom)?.textContent || '';
    const bodyElement = document.querySelector(SELECTORS.emailBody);
    const body = bodyElement?.textContent || '';
    const links = Array.from(document.querySelectorAll(SELECTORS.emailLinks))
        .map(a => a.href);

    if (!body) return null;

    return { subject, from, body, links };
}

/**
 * Extract features from email text
 */
async function extractFeatures(text) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/extract-email-features`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        const data = await response.json();
        if (data.success) {
            return data.features;
        }
        throw new Error('Feature extraction failed');
    } catch (error) {
        console.error('Feature extraction error:', error);
        throw error;
    }
}

/**
 * Scan email using King-Phisher API
 */
async function scanEmail(features, emailData) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/scan-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...features,
                email_subject: emailData.subject,
                email_body: emailData.body
            })
        });

        const data = await response.json();
        if (data.success) {
            return data;
        }
        throw new Error(data.error || 'Scan failed');
    } catch (error) {
        console.error('Scan error:', error);
        throw error;
    }
}

/**
 * Display scan result in Gmail
 */
function displayResult(result, emailData) {
    // Remove existing banner
    const existing = document.getElementById('kingphisher-banner');
    if (existing) existing.remove();

    // Create result banner
    const banner = document.createElement('div');
    banner.id = 'kingphisher-banner';
    banner.className = `kingphisher-banner ${result.prediction ? 'danger' : 'safe'}`;

    const icon = result.prediction ? '⚠️' : '✅';
    const text = result.prediction ? 'PHISHING DETECTED' : 'EMAIL IS SAFE';
    const color = result.prediction ? '#ef4444' : '#16a34a';

    banner.innerHTML = `
    <div style="display: flex; align-items: center; gap: 12px;">
      <span style="font-size: 24px;">${icon}</span>
      <div style="flex: 1;">
        <div style="font-weight: 700; font-size: 16px; color: ${color};">
          ${text}
        </div>
        <div style="font-size: 14px; color: #64748b; margin-top: 4px;">
          Confidence: ${(result.confidence * 100).toFixed(1)}%
        </div>
      </div>
      <button class="kingphisher-close" onclick="this.parentElement.parentElement.remove()">
        ✕
      </button>
    </div>
  `;

    // Insert banner
    const emailBody = document.querySelector(SELECTORS.emailBody);
    if (emailBody) {
        emailBody.parentElement.insertBefore(banner, emailBody);
    }

    // Show browser notification
    if (result.prediction) {
        chrome.runtime.sendMessage({
            type: 'show_notification',
            title: 'Phishing Detected!',
            message: `Email from ${emailData.from} appears to be phishing (${(result.confidence * 100).toFixed(1)}% confidence)`
        });
    }
}

/**
 * Update scan button state
 */
function updateScanButton(state) {
    const button = document.getElementById('kingphisher-scan-btn');
    if (!button) return;

    const icon = button.querySelector('.kingphisher-icon');
    const text = button.querySelector('.kingphisher-text');

    if (state === 'scanning') {
        icon.textContent = '⏳';
        text.textContent = 'Scanning...';
        button.style.opacity = '0.6';
        button.style.pointerEvents = 'none';
    } else {
        icon.textContent = '🛡️';
        text.textContent = 'Scan for Phishing';
        button.style.opacity = '1';
        button.style.pointerEvents = 'auto';
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    chrome.runtime.sendMessage({
        type: 'show_notification',
        title: 'King-Phisher',
        message: message
    });
}

/**
 * Observe DOM changes to detect new emails
 */
function observeEmailChanges() {
    const observer = new MutationObserver((mutations) => {
        // Check if scan button still exists
        if (!document.getElementById('kingphisher-scan-btn')) {
            addScanButton();
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// Initialize when Gmail is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    // Gmail is SPA, wait a bit for it to fully load
    setTimeout(init, 2000);
}

console.log('🛡️ King-Phisher: Content script loaded');
