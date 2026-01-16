/**
 * King-Phisher Chrome Extension - Background Service Worker
 */

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'show_notification') {
        showNotification(request.title, request.message);
    }
});

/**
 * Show browser notification
 */
function showNotification(title, message) {
    chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon128.png',
        title: title,
        message: message,
        priority: 2
    });
}

/**
 * Handle extension installation
 */
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        console.log('🛡️ King-Phisher installed!');

        // Set default settings
        chrome.storage.sync.set({
            autoScan: false,
            apiUrl: 'http://localhost:5000',
            notifications: true
        });

        // Open welcome page
        chrome.tabs.create({
            url: 'http://localhost:5000/dashboard'
        });
    }
});

console.log('🛡️ King-Phisher: Background service worker loaded');
