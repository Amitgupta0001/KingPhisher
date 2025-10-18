// Background message handler
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case 'login':
      return KingPhisherAuth.login(request.credentials)
        .then(sendResponse);
    
    case 'register':
      return KingPhisherAuth.register(request.userData)
        .then(sendResponse);
      
    case 'logout':
      return KingPhisherAuth.logout()
        .then(sendResponse);
      
    case 'getAuthStatus':
      return KingPhisherAuth.isAuthenticated()
        .then(isAuthenticated => sendResponse({ isAuthenticated }));
      
    case 'analyzeEmail':
      return handleEmailAnalysis(request, sendResponse);
      
    case 'reportPhishing':
      return handlePhishingReport(request, sendResponse);
      
    case 'authStateChanged':
      // Broadcast to all tabs/popups
      chrome.tabs.query({}, tabs => {
        tabs.forEach(tab => {
          chrome.tabs.sendMessage(tab.id, request);
        });
      });
      chrome.runtime.sendMessage(request); // For popup
      break;
      
    default:
      console.warn('Unknown action:', request.action);
  }
  return true;
}
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'showPopup') {
      chrome.action.openPopup();
    }
  });