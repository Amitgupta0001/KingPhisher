import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from imblearn.over_sampling import SMOTE
import joblib
import os

# Define consistent paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'email_phishing_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'phishing_model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'scaler.pkl')

def train_model():
    try:
        # Load data
        data = pd.read_csv(DATA_PATH)
        print("Data loaded successfully")
        
        # Preprocessing
        data = data.dropna()
        X = data.drop('label', axis=1)
        y = data['label']
        
        # Feature scaling
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Handle class imbalance
        sm = SMOTE(random_state=42)
        resampled_data = sm.fit_resample(X_scaled, y)
        X_res, y_res = resampled_data[0], resampled_data[1]
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_res, y_res)
        
        # Save artifacts
        joblib.dump(model, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
        print("Model training completed successfully")
        return True
        
    except Exception as e:
        print(f"Error in model training: {str(e)}")
        return False

if __name__ == '__main__':
    train_model()