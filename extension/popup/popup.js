const API_BASE = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', async () => {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const scanBtn = document.getElementById('scanBtn');
    const urlInput = document.getElementById('urlInput');
    const resultCard = document.getElementById('resultCard');
    const historyList = document.getElementById('historyList');
    
    // Auth Elements
    const userEmailSpan = document.getElementById('user-email');
    const logoutBtn = document.getElementById('logoutBtn');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const showRegister = document.getElementById('showRegister');
    const showLogin = document.getElementById('showLogin');
    const doLoginBtn = document.getElementById('doLoginBtn');
    const doRegisterBtn = document.getElementById('doRegisterBtn');

    // Check Auth Status
    await checkAuth();

    // Tab Switching
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    function switchTab(tabId) {
        navButtons.forEach(b => b.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));
        
        const btn = document.querySelector(`[data-tab="${tabId}"]`);
        if (btn) btn.classList.add('active');
        document.getElementById(tabId).classList.add('active');
        
        // Toggle Hero Section visibility to save space
        const hero = document.querySelector('.hero');
        if (tabId === 'history' || tabId === 'login') {
            hero.classList.add('hidden');
        } else {
            hero.classList.remove('hidden');
        }

        if (tabId === 'history') loadHistory();
        if (tabId === 'login') {
            // Default to login form
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
        }
    }

    // Manual Scan
    scanBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) return;

        showLoading();

        try {
            const token = await getAuthToken();
            const headers = { 'Content-Type': 'application/json' };
            if (token) headers['Authorization'] = `Bearer ${token}`;

            const response = await fetch(`${API_BASE}/scan-url`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ url })
            });

            const data = await response.json();
            displayResult(data);
            if (!token) saveToLocalHistory(data); // Fallback to local if not logged in
        } catch (error) {
            console.error('Scan failed:', error);
            displayError('Could not connect to backend.');
        }
    });

    // Auth Actions
    showRegister.onclick = (e) => {
        e.preventDefault();
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
    };

    showLogin.onclick = (e) => {
        e.preventDefault();
        registerForm.classList.add('hidden');
        loginForm.classList.remove('hidden');
    };

    const msgBox = document.getElementById('messageBox');

    const showMsg = (msg, type = 'error') => {
        msgBox.innerText = msg;
        msgBox.className = `message-box ${type}`;
        msgBox.classList.remove('hidden');
        if (type === 'success') {
            setTimeout(() => msgBox.classList.add('hidden'), 10000);
        }
    };

    doLoginBtn.onclick = async () => {
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPass').value;
        msgBox.classList.add('hidden');
        
        try {
            const response = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            if (response.ok) {
                await setAuthToken(data.access_token, email);
                await checkAuth();
                showMsg('Logged in successfully!', 'success');
                switchTab('scan');
            } else {
                const msg = Array.isArray(data.detail) ? data.detail[0].msg : data.detail;
                showMsg(`Login Error: ${msg || 'Invalid credentials'}`);
            }
        } catch (e) {
            showMsg('Connection Error: Is the backend server running?');
        }
    };

    doRegisterBtn.onclick = async () => {
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPass').value;
        msgBox.classList.add('hidden');
        
        try {
            const response = await fetch(`${API_BASE}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            if (response.ok) {
                await setAuthToken(data.access_token, email);
                await checkAuth();
                showMsg('Account created!', 'success');
                switchTab('scan');
            } else {
                const msg = Array.isArray(data.detail) ? data.detail[0].msg : data.detail;
                showMsg(`Registration Error: ${msg || 'Check details'}`);
            }
        } catch (e) {
            showMsg('Connection Error: Is the backend server running?');
        }
    };

    logoutBtn.onclick = async () => {
        await chrome.storage.local.remove(['auth_token', 'user_email']);
        await checkAuth();
        switchTab('scan');
    };

    // UI Helper Functions
    async function checkAuth() {
        const result = await chrome.storage.local.get(['auth_token', 'user_email']);
        if (result.auth_token) {
            userEmailSpan.innerText = result.user_email;
            userEmailSpan.classList.remove('hidden');
            logoutBtn.classList.remove('hidden');
            document.getElementById('nav-login').innerText = '👤 Profile';
        } else {
            userEmailSpan.classList.add('hidden');
            logoutBtn.classList.add('hidden');
            document.getElementById('nav-login').innerText = '👤 Login';
        }
    }

    async function getAuthToken() {
        const result = await chrome.storage.local.get(['auth_token']);
        return result.auth_token;
    }

    async function setAuthToken(token, email) {
        await chrome.storage.local.set({ auth_token: token, user_email: email });
    }

    function showLoading() {
        resultCard.classList.remove('hidden');
        document.getElementById('resultTitle').innerText = 'Analyzing...';
        document.getElementById('resultText').innerText = '';
        document.getElementById('explanationText').innerText = '';
        document.getElementById('confidenceLevel').style.width = '0%';
    }

    function displayResult(data) {
        const title = document.getElementById('resultTitle');
        const text = document.getElementById('resultText');
        const explanation = document.getElementById('explanationText');
        const level = document.getElementById('confidenceLevel');
        const icon = document.getElementById('resultIcon');

        title.innerText = data.is_phishing ? '⚠️ Warning!' : '✅ Safe';
        title.style.color = data.is_phishing ? 'var(--danger)' : 'var(--success)';
        
        text.innerText = data.is_phishing 
            ? 'This URL is highly suspicious.' 
            : 'This URL appears to be safe.';
        
        explanation.innerText = data.explanation;
        
        const confidence = data.confidence * 100;
        level.style.width = `${confidence}%`;
        level.className = 'level ' + (data.is_phishing ? 'danger' : 'safe');
        
        icon.innerText = data.is_phishing ? '🚫' : '🛡️';
    }

    function displayError(msg) {
        document.getElementById('resultTitle').innerText = 'Error';
        document.getElementById('resultText').innerText = msg;
    }

    async function loadHistory() {
        const token = await getAuthToken();
        historyList.innerHTML = '<li class="empty-msg">Loading history...</li>';

        if (token) {
            // Load from Backend
            try {
                const response = await fetch(`${API_BASE}/history`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const history = await response.json();
                    renderHistory(history);
                    return;
                }
            } catch (e) { console.error('Failed to fetch backend history'); }
        }

        // Fallback to Local History
        chrome.storage.local.get(['scanHistory'], (result) => {
            renderHistory(result.scanHistory || [], true);
        });
    }

    function renderHistory(history, isLocal = false) {
        historyList.innerHTML = '';
        if (history.length === 0) {
            historyList.innerHTML = '<li class="empty-msg">No scan history found.</li>';
            return;
        }

        history.forEach(item => {
            const li = document.createElement('li');
            li.className = 'history-item';
            const url = item.target_url || item.url;
            li.innerHTML = `
                <div class="url">${url}</div>
                <span class="badge ${item.is_phishing ? 'danger' : 'safe'}">
                    ${item.is_phishing ? 'Phishing' : 'Safe'}
                </span>
            `;
            historyList.appendChild(li);
        });
    }

    function saveToLocalHistory(data) {
        chrome.storage.local.get(['scanHistory'], (result) => {
            const history = result.scanHistory || [];
            history.unshift({
                url: data.url,
                is_phishing: data.is_phishing,
                time: new Date().toLocaleString()
            });
            chrome.storage.local.set({ scanHistory: history.slice(0, 20) });
        });
    }
});
