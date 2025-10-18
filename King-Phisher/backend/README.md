Email Phishing Detection Extension
Overview
A Chrome extension that sorts emails in Gmail based on AI-powered phishing detection. Features user login/registration and continuous learning from user-labeled emails.
File Structure

extension/: Chrome extension files
manifest.json: Extension configuration
popup.html, popup.js: Main UI for scanning and training
login.html, login.js: Login interface
register.html, register.js: Registration interface
content.js: Extracts email data from Gmail
background.js: Handles extension lifecycle


server/: Backend server files
server.py: Flask server for authentication, prediction, and training
train_model.py: Initial and continuous model training
credentials.json: Gmail API credentials (download from Google Cloud)
users.db: SQLite database (auto-generated)
phishing_model/: BERT model files (auto-generated)



Setup Instructions

Install Dependencies:
Run: pip install flask flask-jwt-extended bcrypt pandas simpletransformers torch google-auth-oauthlib google-api-python-client


Gmail API Setup:
Enable Gmail API in Google Cloud Console.
Download credentials.json and place in server/.


Dataset:
Download phishing/legitimate email dataset (e.g., Phishing Corpus).
Update train_model.py with dataset path.


Train Model:
Run: python server/train_model.py


Run Server:
Set JWT_SECRET_KEY in server.py.
Run: python server/server.py


Install Extension:
Load extension/ folder in Chrome via chrome://extensions/ (Developer mode).


Usage:
Register/login via extension popup.
Scan emails or train model on inbox.



Notes

Security: Use a secure JWT_SECRET_KEY. Run server locally or on a secure host.
Limitations: Gmail API rate limits may restrict email fetching.
Enhancements: Add manual email labeling UI or support for other email platforms.

