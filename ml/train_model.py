import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import os
import sys
import json
from datetime import datetime

# Add backend to path so we can import feature_extractor and constants
sys.path.append(os.getcwd())
from backend.utils.feature_extractor import extract_email_features
from backend.utils.constants import EMAIL_FEATURE_ORDER

def train_email_model():
    dataset1_path = 'data/email_phishing_data.csv'
    dataset2_path = 'data/phishing_email.csv'
    
    dfs = []

    if os.path.exists(dataset1_path):
        print(f"Loading pre-extracted dataset: {dataset1_path}...")
        dfs.append(pd.read_csv(dataset1_path))

    if os.path.exists(dataset2_path):
        print(f"Loading raw text dataset: {dataset2_path}...")
        df2 = pd.read_csv(dataset2_path)
        
        print("Extracting features from raw text (this may take a minute)...")
        features_list = []
        for i, row in df2.iterrows():
            if i % 10000 == 0 and i > 0:
                print(f"  Processed {i} rows...")
            
            text = str(row['text_combined'])
            feat = extract_email_features(text)
            feat['label'] = row['label']
            features_list.append(feat)
        
        df2_extracted = pd.DataFrame(features_list)
        dfs.append(df2_extracted)

    if not dfs:
        print("No datasets found.")
        return

    # Combine datasets
    df = pd.concat(dfs, ignore_index=True)
    print(f"Total training samples: {len(df)}")
    
    # Ensure feature order matches the constant
    X = df[EMAIL_FEATURE_ORDER]
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training Random Forest model on combined features...")
    # Use min_samples_leaf to reduce overfitting
    model = RandomForestClassifier(n_estimators=100, min_samples_leaf=5, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    report = classification_report(y_test, y_pred, output_dict=True)
    print(classification_report(y_test, y_pred))

    # Save the email model
    os.makedirs('backend/model', exist_ok=True)
    joblib.dump(model, 'backend/model/email_model.pkl')
    
    # Save model metadata
    metadata = {
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "accuracy": accuracy,
        "samples": len(df),
        "features": EMAIL_FEATURE_ORDER,
        "metrics": report
    }
    with open('backend/model/email_model_info.json', 'w') as f:
        json.dump(metadata, f, indent=4)

    print("Email model and metadata saved to backend/model/")

if __name__ == "__main__":
    train_email_model()
