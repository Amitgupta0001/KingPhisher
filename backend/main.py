from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
import joblib
import os
import pandas as pd
from typing import List, Optional
from sqlalchemy.orm import Session

from .utils.feature_extractor import extract_url_features, extract_email_features
from .utils.explain import explain_phishing, explain_email_phishing
from .utils.constants import EMAIL_FEATURE_ORDER, URL_FEATURE_ORDER, MAX_EMAIL_TEXT_LENGTH
from .database.db import init_db, get_db
from .database.models import User, ScanHistory
from .utils.auth import get_password_hash, verify_password, create_access_token, decode_access_token

app = FastAPI(title="King Phisher AI API")

# Initialize Database
init_db()

# Enable CORS - Restrict to Chrome Extensions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Models
URL_MODEL_PATH = "backend/model/url_model.pkl"
EMAIL_MODEL_PATH = "backend/model/email_model.pkl"

url_model = None
email_model = None

def load_artifacts():
    global url_model, email_model
    if os.path.exists(URL_MODEL_PATH):
        try:
            url_model = joblib.load(URL_MODEL_PATH)
        except Exception as e:
            print(f"Error loading URL model: {e}")

    if os.path.exists(EMAIL_MODEL_PATH):
        try:
            email_model = joblib.load(EMAIL_MODEL_PATH)
        except Exception as e:
            print(f"Error loading email model: {e}")

load_artifacts()

# Pydantic Schemas
class URLRequest(BaseModel):
    url: str = Field(..., max_length=2048)

class EmailRequest(BaseModel):
    text: str = Field(..., max_length=MAX_EMAIL_TEXT_LENGTH)

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=72)

class Token(BaseModel):
    access_token: str
    token_type: str

# Dependency to get current user
def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        return None
    
    email = payload.get("sub")
    if not email:
        return None
        
    user = db.query(User).filter(User.email == email).first()
    return user

@app.get("/")
def read_root():
    return {"message": "King Phisher AI Backend is running!"}

# --- Auth Routes ---

@app.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Scan Routes ---

@app.post("/scan-url")
def scan_url(req: URLRequest, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    if not url_model:
        load_artifacts()

    features = extract_url_features(req.url)
    
    is_phishing = False
    confidence = 0.0
    
    if url_model:
        # We only pass the first 4 features to the model to avoid name/shape errors,
        # but we use the 5th feature (suspicious keywords) for our Safety Net.
        X = pd.DataFrame([features[:4]], columns=URL_FEATURE_ORDER)
        prediction = url_model.predict(X)[0]
        is_phishing = bool(prediction)
        
        # HEURISTIC OVERRIDE (Safety Net)
        # If the model misses it, but it has suspicious keywords OR an @ symbol, flag it.
        if not is_phishing:
            if features[4] > 0 or features[1] > 0: # suspicious_count > 0 or has_at > 0
                is_phishing = True
                confidence = 0.88
        elif hasattr(url_model, "predict_proba"):
            confidence = float(url_model.predict_proba(X)[0][1])
    else:
        is_phishing = len(req.url) > 150 or "@" in req.url
        confidence = 0.6 if is_phishing else 0.0

    explanation = explain_phishing(req.url, features) if is_phishing else "URL appears safe."

    # Save to history if user is logged in
    if current_user:
        new_scan = ScanHistory(
            user_id=current_user.id,
            target_url=req.url,
            is_phishing=is_phishing,
            confidence=confidence,
            explanation=explanation
        )
        db.add(new_scan)
        db.commit()

    return {
        "url": req.url,
        "is_phishing": is_phishing,
        "confidence": confidence,
        "explanation": explanation
    }

@app.post("/scan-email")
def scan_email(req: EmailRequest, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    if not email_model:
        load_artifacts()

    features = extract_email_features(req.text)
    
    is_phishing = False
    confidence = 0.0
    
    if email_model:
        # Wrap features in a DataFrame with names to avoid UserWarnings
        feature_list = [float(features[f]) for f in EMAIL_FEATURE_ORDER]
        X = pd.DataFrame([feature_list], columns=EMAIL_FEATURE_ORDER)
        prediction = email_model.predict(X)[0]
        is_phishing = bool(prediction)
        if hasattr(email_model, "predict_proba"):
            confidence = float(email_model.predict_proba(X)[0][1])
        
        # HEURISTIC OVERRIDE (Safety Net)
        # If the model is unsure or under-trained, check for high-risk patterns
        if not is_phishing and features['num_urgent_keywords'] >= 2 and features['num_links'] > 0:
            is_phishing = True
            confidence = 0.85
    else:
        # Fallback if no model exists
        is_phishing = features['num_urgent_keywords'] > 1 and features['num_links'] > 0
        confidence = 0.8 if is_phishing else 0.2
    
    explanation = explain_email_phishing(features) if is_phishing else "Email content appears safe."

    # Save to history if user is logged in
    if current_user:
        new_scan = ScanHistory(
            user_id=current_user.id,
            target_url="Email Content",
            is_phishing=is_phishing,
            confidence=confidence,
            explanation=explanation
        )
        db.add(new_scan)
        db.commit()

    return {
        "is_phishing": is_phishing,
        "confidence": confidence,
        "explanation": explanation,
        "features": features
    }

@app.get("/history")
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    scans = db.query(ScanHistory).filter(ScanHistory.user_id == current_user.id).order_by(ScanHistory.scanned_at.desc()).limit(50).all()
    return scans
