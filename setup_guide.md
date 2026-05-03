# 🛠️ Setup & Installation Guide

This guide will walk you through the process of setting up the **King Phisher AI** ecosystem on your local machine.

---

## 📋 Prerequisites
Ensure you have the following installed:
- **Python 3.8+**
- **Google Chrome** (or any Chromium-based browser)
- **pip** (Python package manager)

---

## 1. Backend Configuration
The backend is built with FastAPI. It handles the feature extraction, ML inference, and explainability logic.

### 🔹 Create Virtual Environment
```bash
# From the project root
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 🔹 Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 🔹 Initialize/Train Models
If you are running the project for the first time, you need to generate the ML artifacts:
```bash
# Train the URL and Email models
./venv/bin/python3 ml/init_model.py
./venv/bin/python3 ml/train_model.py
```

### 🔹 Start the Server
```bash
uvicorn backend.main:app --reload
```
> **Note**: The backend will run at `http://localhost:8000`. Keep this terminal open.

---

## 2. Extension Installation
The Chrome Extension acts as the "front-line" defense.

1.  Open Chrome and navigate to `chrome://extensions/`.
2.  Toggle the **Developer mode** switch in the top-right corner.
3.  Click the **Load unpacked** button.
4.  Select the `extension` folder from the `KingPhisher` project directory.
5.  The **King Phisher AI** icon should now appear in your extension toolbar.

---

## 3. How to Verify Installation

### ✅ Manual Scan Test
1.  Click the King Phisher icon in your browser toolbar.
2.  Paste a suspicious URL (e.g., `http://verify-account.com@malicious-site.net`).
3.  Click **Analyze**. You should see a phishing warning and a detailed explanation.

### ✅ Real-time URL Test
Navigate to any website. Open the browser console (`F12` -> Console). You should see:
`King Phisher AI: Auto-scan complete.`

### ✅ Gmail Scanner Test
1.  Open [Gmail](https://mail.google.com).
2.  Open any email. You will see a small console log: `King Phisher AI: Gmail detected.`
3.  If an email contains phishing patterns, a red warning banner will be prepended to the email body.

### ✅ Account Synchronization Test
1.  Open the extension popup and click on the **Account** tab.
2.  Click **Register** and create a test account.
3.  Perform a scan while logged in.
4.  Navigate to the **History** tab. You should see your scan history fetched directly from the backend database!

---

## ⚠️ Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **"Could not connect to backend"** | Ensure the FastAPI server is running on port 8000. |
| **"Model not found"** | Check `backend/model/`. If empty, run the scripts in the `ml/` folder. |
| **Extension not scanning** | Refresh the tab or ensure the site is not a `chrome://` internal page. |
| **Gmail Banner not appearing** | Ensure you are using the standard Gmail web interface. |

---
**Happy Hunting!** 👑🛡️
