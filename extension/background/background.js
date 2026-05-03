chrome.runtime.onInstalled.addListener(() => {
    console.log('King Phisher AI Extension installed.');
    chrome.storage.local.set({ 
        scanHistory: [],
        settings: {
            realtimeEnabled: true,
            emailNotifications: true
        }
    });
});

// Handle messages from popup or content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'notifyPhishing') {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: '/assets/icon128.png',
            title: '⚠️ Phishing Alert!',
            message: request.message,
            priority: 2
        });
    }
});

// Listener for tab updates to trigger scanning if needed (can also be done in content script)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        // Log for debugging
        console.log('Tab updated:', tab.url);
    }
});
