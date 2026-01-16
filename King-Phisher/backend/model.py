import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    precision_score, recall_score, f1_score, roc_auc_score, roc_curve
)
from imblearn.over_sampling import SMOTE
import joblib
import os
import json
from datetime import datetime
import numpy as np

# Define consistent paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'email_phishing_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'phishing_model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'scaler.pkl')
METRICS_PATH = os.path.join(BASE_DIR, 'model_metrics.json')

def train_model():
    """Train phishing detection model with comprehensive evaluation."""
    try:
        print("="*60)
        print("KING-PHISHER MODEL TRAINING")
        print("="*60)
        
        # Load data
        data = pd.read_csv(DATA_PATH)
        print(f"✓ Data loaded successfully: {len(data)} samples")
        
        # Preprocessing
        data = data.dropna()
        print(f"✓ After removing NaN: {len(data)} samples")
        
        X = data.drop('label', axis=1)
        y = data['label']
        
        # Check class distribution
        class_dist = y.value_counts()
        print(f"\nClass Distribution:")
        print(f"  Safe (0): {class_dist.get(0, 0)} ({class_dist.get(0, 0)/len(y)*100:.1f}%)")
        print(f"  Phishing (1): {class_dist.get(1, 0)} ({class_dist.get(1, 0)/len(y)*100:.1f}%)")
        
        # Feature scaling
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        print(f"✓ Features scaled")
        
        # Handle class imbalance with SMOTE
        sm = SMOTE(random_state=42)
        X_res, y_res = sm.fit_resample(X_scaled, y)
        print(f"✓ SMOTE applied: {len(X_res)} balanced samples")
        
        # Split for evaluation (stratified)
        X_train, X_test, y_train, y_test = train_test_split(
            X_res, y_res, test_size=0.2, random_state=42, stratify=y_res
        )
        print(f"✓ Train/Test split: {len(X_train)}/{len(X_test)} samples")
        
        # Train model
        print("\nTraining RandomForest model...")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        print("✓ Model trained successfully")
        
        # Evaluate on test set
        print("\nEvaluating model...")
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        cm = confusion_matrix(y_test, y_pred)
        
        # Feature importance
        feature_importance = dict(zip(X.columns, model.feature_importances_))
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        # Print results
        print("\n" + "="*60)
        print("MODEL EVALUATION RESULTS")
        print("="*60)
        print(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"Precision: {precision:.4f} ({precision*100:.2f}%)")
        print(f"Recall:    {recall:.4f} ({recall*100:.2f}%)")
        print(f"F1-Score:  {f1:.4f} ({f1*100:.2f}%)")
        print(f"ROC-AUC:   {roc_auc:.4f}")
        
        print(f"\nConfusion Matrix:")
        print(f"  TN: {cm[0][0]:5d}  |  FP: {cm[0][1]:5d}")
        print(f"  FN: {cm[1][0]:5d}  |  TP: {cm[1][1]:5d}")
        
        print(f"\nTop 5 Important Features:")
        for feature, importance in sorted_features[:5]:
            print(f"  {feature:25s}: {importance:.4f}")
        
        # Prepare metrics for saving
        metrics = {
            'model_version': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'trained_at': datetime.now().isoformat(),
            'training_samples': int(len(X_train)),
            'test_samples': int(len(X_test)),
            'original_samples': int(len(data)),
            'features': list(X.columns),
            'performance': {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'roc_auc': float(roc_auc)
            },
            'confusion_matrix': {
                'true_negative': int(cm[0][0]),
                'false_positive': int(cm[0][1]),
                'false_negative': int(cm[1][0]),
                'true_positive': int(cm[1][1])
            },
            'feature_importance': {k: float(v) for k, v in feature_importance.items()},
            'class_distribution': {
                'original': {
                    'safe': int(class_dist.get(0, 0)),
                    'phishing': int(class_dist.get(1, 0))
                },
                'after_smote': {
                    'safe': int(sum(y_res == 0)),
                    'phishing': int(sum(y_res == 1))
                }
            },
            'model_params': model.get_params()
        }
        
        # Save metrics
        with open(METRICS_PATH, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"\n✓ Metrics saved to: {METRICS_PATH}")
        
        # Save model artifacts
        joblib.dump(model, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
        print(f"✓ Model saved to: {MODEL_PATH}")
        print(f"✓ Scaler saved to: {SCALER_PATH}")
        
        print("\n" + "="*60)
        print("MODEL TRAINING COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error in model training: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = train_model()
    exit(0 if success else 1)