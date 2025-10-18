# King-Phisher (Backend) — Architecture & Setup

## Overview
A Flask-based web app for phishing detection with:
- Authentication (Flask-Login) and SQLite storage
- Email-feature ML model (scikit-learn + SMOTE) trained on 8 engineered features
- UI templates for login/register/dashboard/scan
- Helpers to extract features from pasted email text and (optionally) from URLs

## Tech Stack
- Backend: Flask, Flask-Login, Flask-CORS, Jinja2
- Database: SQLite (`users.db`)
- ML: scikit-learn (RandomForest + StandardScaler), imbalanced-learn (SMOTE), pandas, numpy, joblib
- Feature helpers: tldextract, python-whois (domain age), optional pyspellchecker
- Frontend: HTML/CSS/JS templates in `templates/`

## Important Paths
- App entry: `backend/app.py`
- Templates: `backend/templates/`
- Data: `backend/email_phishing_data.csv`
- Model artifacts: `backend/phishing_model.pkl`, `backend/scaler.pkl`
- Training: `backend/model.py` (called by `backend/train_model.py`)
- Requirements: `backend/requirements.txt`

## Data & Features (Model)
Trained columns in `email_phishing_data.csv`:
- `num_words`
- `num_unique_words`
- `num_stopwords`
- `num_links`
- `num_unique_domains`
- `num_email_addresses`
- `num_spelling_errors`
- `num_urgent_keywords`
- `label` (target)

Inference must supply the same 8 features, in the same order. The current Scan page provides an Auto-Extract button for these.

## Key Endpoints
- Pages
  - `GET /login`, `POST /login`
  - `GET /register`, `POST /register`
  - `GET /dashboard` (auth required)
  - `GET|POST /scan` (auth required)
- APIs
  - `GET /api/domain-age?url=...` → `{ age_days }` (WHOIS-based)
  - `POST /api/extract-email-features` with `{ text }` → `{ features }`

## Running Locally
1) Open a terminal in `backend/`:
```
Set-Location "c:\Users\prabh\OneDrive\Desktop\King_Phisher\King-Phisher\backend"
```
2) Install dependencies:
```
pip install -r requirements.txt
```
3) Start the server:
```
python app.py
```
4) Open the app:
- http://localhost:5000/

## Using the Scan Page
- Paste email text → click "Auto-Extract Email Features" → Review values → "Run Scan".
- URL inputs are optional and not used by the current model.

## Retraining (Optional)
If you change the dataset or features:
```
python train_model.py
```
This overwrites `phishing_model.pkl` and `scaler.pkl`.

## Notes & Security
- Set a persistent `SECRET_KEY` in production (do not use `os.urandom(24)`)
- Use a production WSGI server (e.g., gunicorn/uwsgi) and proper TLS
- WHOIS lookups may be rate-limited
