from flask import Flask, render_template, request, jsonify, send_from_directory, redirect
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import sqlite3
import bcrypt
import re
import pandas as pd
import joblib
from dotenv import load_dotenv
import os
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE
import logging
from typing import Optional, Dict, Any

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY", "zJ9GUhl1yeAxJOrSsbx0WJlh2cvMC4I6jHHwwnc0bDc"
)
jwt = JWTManager(app)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")
MODEL_PATH = os.path.join(BASE_DIR, "phishing_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
DATA_PATH = os.path.join(BASE_DIR, "email_phishing_data.csv")

# Global variables for model and scaler
model: Optional[RandomForestClassifier] = None
scaler: Optional[Any] = None  # Type hint for scikit-learn scaler


def init_db() -> None:
    """Initialize the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS users 
                     (email TEXT PRIMARY KEY, password TEXT)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS emails 
                     (email TEXT, text TEXT, label INTEGER, 
                     FOREIGN KEY(email) REFERENCES users(email))"""
        )
        conn.commit()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
    finally:
        if "conn" in locals():
            conn.close()


def load_model() -> bool:
    """Load the ML model and scaler from disk."""
    global model, scaler
    try:
        if not all(os.path.exists(p) for p in [MODEL_PATH, SCALER_PATH]):
            logger.error("Model or scaler file not found")
            return False

        logger.info(f"Loading model from {MODEL_PATH}")
        model = joblib.load(MODEL_PATH)
        logger.info(f"Loading scaler from {SCALER_PATH}")
        scaler = joblib.load(SCALER_PATH)
        return True

    except Exception as e:
        logger.error(f"Error loading model/scaler: {str(e)}")
        model = None
        scaler = None
        return False


def extract_features(subject: str, body: str, urls: list) -> Dict[str, int]:
    """Extract features from email content for prediction."""
    text = f"{subject} {body}".lower()
    stop_words = {"the", "is", "and", "to", "of", "a", "in", "that", "for"}
    url_domains = set(re.findall(r"(?:http|https)://([^\s/]+)", " ".join(urls)))

    return {
        "num_words": len(text.split()),
        "num_unique_words": len(set(text.split())),
        "num_stopwords": sum(1 for word in text.split() if word in stop_words),
        "num_links": len(urls),
        "num_unique_domains": len(url_domains),
        "num_email_addresses": len(re.findall(r"[\w\.-]+@[\w\.-]+", text)),
        "num_spelling_errors": 0,  # Placeholder for actual implementation
        "num_urgent_keywords": sum(
            1 for word in ["urgent", "immediate", "action", "verify"] if word in text
        ),
    }


# Initialize application components
init_db()
if not load_model():
    logger.warning("Server starting without ML model loaded")



@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        # Serve the login HTML page
        return render_template("login.html")

    # POST: handle login logic
    try:
        data = request.get_json() or request.form  # Supports JSON or form data
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not email or not password:
            return jsonify({"message": "Email and password required"}), 400

        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE email = ?", (email,))
            result = c.fetchone()

        if result:
            stored = result[0]
            if isinstance(stored, str):
                stored = stored.encode("utf-8")
            if bcrypt.checkpw(password.encode("utf-8"), stored):
                access_token = create_access_token(identity=email)
                # If it's a standard HTML form submit, redirect to index instead of returning JSON
                if request.is_json:
                    return jsonify({"access_token": access_token}), 200
                return redirect("/index.html")
        # Invalid credentials
        return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        print(f"Login error: {str(e)}")

        return jsonify({"message": "Login failed"}), 500
# API Endpoints


@app.route("/register.html", methods=["GET", "POST"])
def register():
    
    if request.method == "GET":
        # Serve the login HTML page
        return render_template("register.html")
    """User registration endpoint."""
    try:
        data = request.get_json() or request.form
        email = (data.get("email", "").strip() if data else "")
        password = (data.get("password", "").strip() if data else "")

        if not email or not password:
            return jsonify({"message": "Email and password required"}), 400

        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT email FROM users WHERE email = ?", (email,))
            if c.fetchone():
                return jsonify({"message": "User already exists"}), 400

            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            c.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed)
            )
            conn.commit()

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"message": "Registration failed"}), 500



@app.route("/predict", methods=["POST"])
@jwt_required()
def predict():
    """Phishing prediction endpoint."""
    if model is None or scaler is None:
        return jsonify({"message": "Prediction service unavailable"}), 503

    try:
        data = request.get_json()
        subject = data.get("subject", "")
        body = data.get("body", "")
        urls = data.get("urls", [])

        # Extract features and predict
        features = extract_features(subject, body, urls)
        feature_df = pd.DataFrame([features])
        feature_scaled = scaler.transform(feature_df)

        prediction = model.predict(feature_scaled)[0]
        confidence = float(model.predict_proba(feature_scaled)[0][prediction])

        # Check for suspicious URLs
        suspicious_urls = [
            url
            for url in urls
            if re.search(r"(http|https)://[^\s]*\.[^\s]{2,}", url)
            and "login" in url.lower()
        ]

        if suspicious_urls:
            prediction = 1
            confidence = max(confidence, 0.9)

        # Store prediction in database
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO emails (email, text, label) VALUES (?, ?, ?)",
                (request.get_jwt_identity(), f"{subject} {body}", prediction),
            )
            conn.commit()

        return jsonify(
            {
                "prediction": int(prediction),
                "confidence": confidence,
                "suspicious_urls_found": bool(suspicious_urls),
            }
        )

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({"message": "Prediction failed"}), 500


@app.route("/train", methods=["POST"])
@jwt_required()
def train():
    """Model retraining endpoint."""
    try:
        if not os.path.exists(DATA_PATH):
            return jsonify({"message": "Training data not found"}), 404

        data = pd.read_csv(DATA_PATH)
        X = data.drop("label", axis=1)
        y = data["label"]

        # Get user-submitted emails
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT text, label FROM emails WHERE email = ?",
                (request.get_jwt_identity(),),
            )
            emails = c.fetchall()

        # Prepare new training data
        new_data = []
        for text, label in emails:
            features = extract_features(text, "", [])
            features["label"] = label
            new_data.append(features)

        if new_data:
            new_df = pd.DataFrame(new_data)
            X = pd.concat([X, new_df.drop("label", axis=1)], ignore_index=True)
            y = pd.concat([y, new_df["label"]], ignore_index=True)

            # Scale features and handle class imbalance
            global scaler
            if scaler is None:
                scaler = (
                    joblib.load(SCALER_PATH)
                    if os.path.exists(SCALER_PATH)
                    else StandardScaler()
                )
            if scaler is None:
                scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            sm = SMOTE(random_state=42)
            resampled_data = sm.fit_resample(X_scaled, y)
            X_res, y_res = resampled_data[0], resampled_data[1]

            # Retrain model
            global model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_res, y_res)

            # Save updated model
            joblib.dump(model, MODEL_PATH)
            joblib.dump(scaler, SCALER_PATH)

            return jsonify({"message": "Model retrained successfully"})

        return jsonify({"message": "No new data to train on"})

    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        return jsonify({"message": "Model training failed"}), 500


@app.route("/index.html", methods=["GET"])
def index_page():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
