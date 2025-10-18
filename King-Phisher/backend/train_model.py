import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from imblearn.over_sampling import SMOTE
import joblib
import os
import warnings
from model import train_model  # Reuse the training function

warnings.filterwarnings('ignore')

if __name__ == '__main__':
    if train_model():
        print("Model trained and saved successfully")
    else:
        print("Model training failed")