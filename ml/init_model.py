import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import os
import sys

# Add backend to path
sys.path.append(os.getcwd())
from backend.utils.constants import URL_FEATURE_ORDER

# Create dummy data for the URL model
# Features: [url_length, has_at, has_dash, has_https]
data = {
    'url_length': [10, 15, 120, 150, 20, 180, 25, 200],
    'has_at': [0, 0, 1, 1, 0, 1, 0, 1],
    'has_dash': [0, 0, 1, 1, 0, 1, 0, 1],
    'has_https': [1, 1, 0, 0, 1, 0, 1, 0],
    'is_phishing': [0, 0, 1, 1, 0, 1, 0, 1]
}

df = pd.DataFrame(data)
X = df[URL_FEATURE_ORDER]
y = df['is_phishing']

model = RandomForestClassifier(n_estimators=10, random_state=42)
model.fit(X, y)

# Save model
os.makedirs('backend/model', exist_ok=True)
joblib.dump(model, 'backend/model/url_model.pkl')

print("URL model trained and saved with correct feature names.")
