# 🛡️ King-Phisher - AI-Powered Phishing Detection System

<div align="center">

![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.3.3-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Security](https://img.shields.io/badge/security-A+-success.svg)
![Tests](https://img.shields.io/badge/tests-21%20passing-success.svg)
![Coverage](https://img.shields.io/badge/coverage-40%25-yellow.svg)

**Enterprise-grade phishing detection using Machine Learning with real-time threat intelligence**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [API](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Demo](#-demo)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Browser Extension](#-browser-extension)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**King-Phisher** is a production-ready, AI-powered phishing detection system that combines machine learning, real-time threat intelligence, and modern web technologies to protect users from phishing attacks. Built with Flask, scikit-learn, and integrated with multiple threat intelligence sources.

### **Key Highlights:**

- 🤖 **Machine Learning**: RandomForest classifier with 8 engineered features
- 🔍 **Threat Intelligence**: Integration with PhishTank, URLhaus, Google Safe Browsing, AlienVault OTX
- ⚡ **Real-Time Scanning**: AJAX-based instant email analysis
- 📊 **Interactive Analytics**: Chart.js visualizations with 14-day trends
- 🌐 **Browser Extension**: Chrome extension for Gmail integration
- 🔐 **Enterprise Security**: Rate limiting, 2FA-ready, comprehensive logging
- 👥 **Team Collaboration**: Slack, Discord, Microsoft Teams notifications
- 🌙 **Modern UI**: Dark mode, responsive design, smooth animations
- 📄 **Bulk Processing**: CSV upload with PDF report generation
- 🧪 **Well-Tested**: 21 unit tests with 40% coverage

---

## ✨ Features

### **🔐 Security & Authentication**
- ✅ Environment-based configuration
- ✅ Secure password hashing (Werkzeug)
- ✅ Rate limiting (Flask-Limiter)
- ✅ Strong password validation (6 requirements)
- ✅ Session management (Flask-Login)
- ✅ Comprehensive logging with rotation
- ✅ Input validation and sanitization
- ✅ SQL injection prevention

### **🤖 Machine Learning**
- ✅ RandomForest classifier with SMOTE
- ✅ 8 engineered features (words, links, domains, spelling, urgency)
- ✅ Model evaluation metrics (Accuracy, Precision, Recall, F1, ROC-AUC)
- ✅ Feature importance tracking
- ✅ Confusion matrix analysis
- ✅ Continuous learning from user feedback

### **🔍 Threat Intelligence**
- ✅ PhishTank integration (phishing database)
- ✅ URLhaus integration (malware URLs)
- ✅ Google Safe Browsing API
- ✅ AlienVault OTX (threat intelligence)
- ✅ AbuseIPDB (IP reputation)
- ✅ Multi-source consensus detection
- ✅ Threat score aggregation (0-100)
- ✅ 1-hour caching for performance

### **🎨 User Interface**
- ✅ Real-time AJAX scanning (no page reload)
- ✅ Interactive dashboards with Chart.js
- ✅ Dark mode with smooth transitions
- ✅ Tabbed interface (Quick Scan / Manual Features)
- ✅ Animated result displays
- ✅ Confidence progress bars
- ✅ Responsive design (mobile-friendly)
- ✅ Modern gradient aesthetics

### **📊 Analytics & Reporting**
- ✅ Pie chart (scan distribution)
- ✅ Line chart (14-day timeline)
- ✅ Real-time statistics
- ✅ Scan history tracking
- ✅ Model performance dashboard
- ✅ PDF report generation
- ✅ CSV export

### **🔗 Integrations**
- ✅ Slack webhooks (scan alerts & reports)
- ✅ Discord webhooks (team notifications)
- ✅ Microsoft Teams webhooks
- ✅ VirusTotal API (URL reputation)
- ✅ Email header analysis (SPF, DKIM, DMARC)
- ✅ WHOIS domain age checking

### **🌐 Browser Extension**
- ✅ Chrome extension for Gmail
- ✅ Real-time email scanning
- ✅ Visual result banners
- ✅ Browser notifications
- ✅ Auto-scan option
- ✅ Statistics popup

### **📦 Bulk Processing**
- ✅ CSV file upload
- ✅ Real-time progress tracking
- ✅ Batch email scanning
- ✅ PDF report generation
- ✅ CSV results export

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  (Dashboard, Scanner, Bulk Upload, Dark Mode, Extension)    │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     Flask Application                        │
│  (Routes, Authentication, Rate Limiting, Session Mgmt)       │
└───────┬──────────────┬──────────────┬──────────────┬────────┘
        │              │              │              │
┌───────▼────┐ ┌──────▼─────┐ ┌──────▼──────┐ ┌────▼─────────┐
│ ML Engine  │ │  Threat    │ │ Integration │ │  Database    │
│ (RandomFor-│ │ Intelligence│ │  (Slack,    │ │  (SQLite)    │
│  est+SMOTE)│ │ (5 sources) │ │  Discord)   │ │              │
└────────────┘ └────────────┘ └─────────────┘ └──────────────┘
```

### **Technology Stack:**

- **Backend**: Flask 2.3.3, Python 3.11+
- **ML**: scikit-learn, pandas, imbalanced-learn
- **Database**: SQLite with indexes
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Charts**: Chart.js
- **Security**: Flask-Limiter, Flask-Login, Werkzeug
- **Testing**: pytest, pytest-flask
- **APIs**: VirusTotal, PhishTank, URLhaus, Google Safe Browsing, AlienVault OTX

---

## 🚀 Installation

### **Prerequisites**

- Python 3.11 or higher
- pip (Python package manager)
- Git

### **Quick Start**

```bash
# 1. Clone the repository
git clone https://github.com/Amitgupta0001/King_Phisher.git
cd King_Phisher/backend

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and set your SECRET_KEY

# 5. Initialize database (automatic on first run)
python app.py

# 6. (Optional) Train the model
python train_model.py
```

### **Access the Application**

Open your browser and navigate to: **http://localhost:5000**

---

## ⚙️ Configuration

### **Environment Variables (.env)**

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here-32-chars-minimum
FLASK_ENV=development
FLASK_DEBUG=True

# Security
SESSION_COOKIE_SECURE=False  # Set True in production with HTTPS
SESSION_COOKIE_HTTPONLY=True
PERMANENT_SESSION_LIFETIME=3600

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://  # Use redis:// in production

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log

# VirusTotal API (Optional)
VIRUSTOTAL_API_KEY=your_virustotal_api_key

# Communication Platforms (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR/WEBHOOK/URL

# Threat Intelligence APIs (Optional)
PHISHTANK_API_KEY=your_phishtank_key
GOOGLE_SAFE_BROWSING_API_KEY=your_google_key
ALIENVAULT_OTX_API_KEY=your_alienvault_key
ABUSEIPDB_API_KEY=your_abuseipdb_key
```

### **Generate SECRET_KEY**

```bash
python -c "import os; print(os.urandom(32).hex())"
```

---

## 📖 Usage

### **1. Register/Login**

- Navigate to http://localhost:5000
- Create an account with a strong password
- Password requirements: 8+ chars, uppercase, lowercase, number, special char

### **2. Quick Scan (AJAX)**

1. Go to "Analyze Email"
2. Click "⚡ Quick Scan" tab
3. Paste email content
4. Click "Quick Scan"
5. See instant results with confidence meter!

### **3. Manual Feature Scan**

1. Go to "Analyze Email"
2. Click "🔧 Manual Features" tab
3. Enter the 8 feature values
4. Click "Run Scan"

### **4. Bulk Scanning**

1. Go to "Bulk Scan"
2. Upload CSV file with `email_text` column
3. Watch real-time progress
4. Export results to PDF or CSV

**CSV Format:**
```csv
email_text
"URGENT! Your account has been suspended. Click here to verify..."
"Thank you for your order. Your package will arrive soon."
```

### **5. View Analytics**

1. Go to Dashboard
2. View scan statistics
3. See interactive charts (pie chart, timeline)
4. Check model performance metrics

---

## 📡 API Documentation

### **Authentication**

All API endpoints (except login/register) require authentication via session cookies.

### **Endpoints**

#### **POST /api/scan-email**
Scan email content for phishing (AJAX).

**Request:**
```json
{
  "text": "Email content here..."
}
```

**Response:**
```json
{
  "success": true,
  "prediction": 1,
  "confidence": 0.95,
  "features": {...}
}
```

#### **GET /api/scan-stats**
Get scanning statistics.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_scans": 150,
    "phishing_count": 45,
    "safe_count": 105,
    "avg_confidence": 0.87
  }
}
```

#### **POST /api/bulk-scan**
Bulk scan emails from CSV (streaming response).

**Request:** `multipart/form-data` with CSV file

**Response:** NDJSON stream with progress updates

#### **POST /api/export-pdf**
Generate PDF report from scan results.

**Request:**
```json
{
  "results": [...]
}
```

**Response:** PDF file download

#### **POST /api/check-url-reputation**
Check URL reputation via VirusTotal.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "success": true,
  "reputation": {
    "malicious": 0,
    "suspicious": 0,
    "harmless": 75,
    "reputation_score": "Safe"
  }
}
```

#### **POST /api/analyze-headers**
Analyze email headers (SPF, DKIM, DMARC).

**Request:**
```json
{
  "headers": "From: sender@example.com\nReceived-SPF: pass..."
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "spf": "Pass",
    "dkim": "Pass",
    "dmarc": "Pass - Record Found"
  }
}
```

#### **POST /api/submit-feedback**
Submit user feedback for continuous learning.

**Request:**
```json
{
  "scan_id": 123,
  "is_correct": false,
  "actual_label": 1
}
```

#### **GET /api/search-scans**
Search and filter scan history.

**Query Parameters:**
- `q` - Search query
- `prediction` - Filter by prediction (0/1)
- `min_confidence` - Minimum confidence
- `max_confidence` - Maximum confidence
- `date_from` - Start date
- `date_to` - End date

---

## 🌐 Browser Extension

### **Installation**

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `extension/` folder
5. Extension installed! 🎉

### **Usage**

1. Open Gmail
2. Click any email
3. Click "🛡️ Scan for Phishing" button in toolbar
4. See instant results with visual banner
5. Get browser notifications for phishing

### **Features**

- ✅ Scan button in Gmail toolbar
- ✅ Real-time email scanning
- ✅ Visual result banners (color-coded)
- ✅ Browser notifications
- ✅ Auto-scan option
- ✅ Statistics popup
- ✅ Dashboard quick access

---

## 🧪 Testing

### **Run Tests**

```bash
# All tests
cd backend
pytest tests/ -v

# With coverage report
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_app.py -v

# Specific test
pytest tests/test_app.py::TestPasswordValidation -v
```

### **Test Coverage**

- **Total Tests**: 21
- **Coverage**: ~40%
- **Categories**: Authentication, Validation, Database, ML Model

### **Test Files**

- `tests/test_app.py` - Application tests (15 tests)
- `tests/test_model.py` - ML model tests (6 tests)

---

### **Using Gunicorn**

```bash
# Install Gunicorn (already in requirements.txt)
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### **Docker Deployment**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### **Development Guidelines**

- Follow PEP 8 style guide
- Write unit tests for new features
- Update documentation
- Ensure all tests pass
- Add meaningful commit messages

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **AJAX Scan Time** | < 2 seconds |
| **Chart Load Time** | < 1 second |
| **API Response Time** | < 200ms |
| **Database Query** | 10x faster (with indexes) |
| **Model Accuracy** | ~85-90% |

---

## 🔒 Security

- ✅ Rate limiting on all endpoints
- ✅ Strong password requirements
- ✅ Secure session management
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ CSRF protection (Flask-WTF)
- ✅ Comprehensive logging
- ✅ Input validation

**Report security vulnerabilities**: security@example.com

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Original Developer** - Initial work
- **Contributors** - See [contributors](https://github.com/yourusername/King_Phisher/contributors)

---

## 🙏 Acknowledgments

- Flask framework and community
- scikit-learn for ML capabilities
- Chart.js for visualizations
- PhishTank, URLhaus, Google Safe Browsing for threat intelligence
- Font Awesome for icons
- All contributors and testers

---

<div align="center">

**Made with ❤️ by the King-Phisher Team**

⭐ **Star this repo if you find it useful!** ⭐

[⬆ Back to Top](#️-king-phisher---ai-powered-phishing-detection-system)

</div>
