class KingPhisherContent {
  constructor() {
    this.initialize();
  }

  async initialize() {
    this.injectStyles();
    this.setupMessageListener();
    
    const isAuthenticated = await this.checkAuthentication();
    if (isAuthenticated) {
      this.injectUI();
    } else {
      this.showAuthPrompt();
    }
  }

  injectStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .king-phisher-btn-group {
        display: flex;
        gap: 8px;
        padding: 8px;
      }
      .kp-btn {
        padding: 6px 12px;
        border-radius: 4px;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .kp-scan-btn {
        background: #4a6bff;
        color: white;
        border: none;
      }
      .kp-report-btn {
        background: #f56565;
        color: white;
        border: none;
      }
      .kp-auth-prompt {
        padding: 8px;
        background: #fef3c7;
        color: #92400e;
        font-size: 14px;
        text-align: center;
      }
    `;
    document.head.appendChild(style);
  }

  async checkAuthentication() {
    try {
      const { isAuthenticated } = await chrome.runtime.sendMessage({action: 'getAuthStatus'});
      return isAuthenticated;
    } catch (error) {
      console.error('Auth check failed:', error);
      return false;
    }
  }

  injectUI() {
    // Gmail injection
    if (window.location.host.includes('mail.google.com')) {
      this.injectGmailUI();
    }
    // Outlook injection
    else if (window.location.host.includes('outlook')) {
      this.injectOutlookUI();
    }
  }

  injectGmailUI() {
    const toolbar = document.querySelector('.G-tF');
    if (toolbar && !document.getElementById('king-phisher-toolbar')) {
      const container = document.createElement('div');
      container.id = 'king-phisher-toolbar';
      container.innerHTML = `
        <div class="king-phisher-btn-group">
          <button id="kp-scan-btn" class="kp-btn kp-scan-btn">
            <img src="${chrome.runtime.getURL('assets/icons/crown-icon.png')}" width="16" alt="Scan">
            Scan Email
          </button>
          <button id="kp-report-btn" class="kp-btn kp-report-btn">
            <i class="fas fa-flag"></i>
            Report
          </button>
        </div>
      `;
      toolbar.prepend(container);
      
      document.getElementById('kp-scan-btn').addEventListener('click', () => this.handleScan());
      document.getElementById('kp-report-btn').addEventListener('click', () => this.handleReport());
    }
  }

  injectOutlookUI() {
    // Similar implementation for Outlook
    console.log('Outlook UI injection would go here');
  }

  showAuthPrompt() {
    const prompt = document.createElement('div');
    prompt.className = 'kp-auth-prompt';
    prompt.innerHTML = `
      Please <a href="${chrome.runtime.getURL('pages/login.html')}" target="_blank">login</a>
      to use King-Phisher features
    `;
    document.body.prepend(prompt);
  }

  setupMessageListener() {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'extractEmail') {
        sendResponse(this.extractEmailData());
      }
      return true;
    });
  }

  async handleScan() {
    try {
      const result = await chrome.runtime.sendMessage({
        action: 'scanCurrentEmail'
      });
      this.showScanResult(result);
    } catch (error) {
      console.error('Scan failed:', error);
    }
  }

  async handleReport() {
    try {
      await chrome.runtime.sendMessage({
        action: 'reportPhishing'
      });
      this.showNotification('Phishing reported successfully');
    } catch (error) {
      console.error('Report failed:', error);
    }
  }

  extractEmailData() {
    try {
      const emailElement = document.querySelector('div[data-message-id]');
      if (!emailElement) return null;

      return {
        subject: document.querySelector('h2.hP')?.innerText || '',
        body: document.querySelector('.a3s.aiL')?.innerText || '',
        sender: document.querySelector('.gD')?.getAttribute('email') || '',
        urls: Array.from(document.querySelectorAll('a'))
          .map(a => a.href)
          .filter(href => href.startsWith('http'))
      };
    } catch (error) {
      console.error('Error extracting email:', error);
      return null;
    }
  }

  showScanResult(result) {
    // Implement result display in email client UI
    console.log('Scan result:', result);
  }

  showNotification(message) {
    // Implement notification display
    console.log('Notification:', message);
  }
}

// Initialize
new KingPhisherContent();