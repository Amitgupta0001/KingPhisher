from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_file
from flask_cors import CORS
import pandas as pd
import joblib
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import re
import tldextract
import logging
from logging.handlers import RotatingFileHandler
import json
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

try:
    import whois  # python-whois package
except Exception:
    whois = None
try:
    from spellchecker import SpellChecker  # pyspellchecker
except Exception:
    SpellChecker = None

# Load environment variables
load_dotenv()

# Lightweight English stopword list to avoid runtime downloads
STOPWORDS = {
    'the','a','an','and','or','but','if','then','so','because','as','of','on','in','for','to','from','by','with',
    'at','this','that','these','those','is','are','was','were','be','been','being','it','its','you','your','yours',
    'we','our','ours','they','their','theirs','he','him','his','she','her','hers','i','me','my','mine','do','does',
    'did','doing','have','has','had','having','will','would','can','could','should','may','might','must','not','no',
    'up','down','out','over','under','again','further','then','once','here','there','when','where','why','how','all',
    'any','both','each','few','more','most','other','some','such','only','own','same','than','too','very'
}

URGENT_KEYWORDS = {
    'urgent','immediately','verify','suspended','confirm','update','password','account','limited','warning',
    'important','action required','immediate action','reset','security alert','unusual activity','deadline'
}

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration from environment
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
app.config['PERMANENT_SESSION_LIFETIME'] = int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600))
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Setup logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_file = os.getenv('LOG_FILE', 'app.log')

if not app.debug:
    file_handler = RotatingFileHandler(log_file, maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(getattr(logging, log_level))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, log_level))
    app.logger.info('King-Phisher startup')

# Initialize Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
)

# Configure Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database setup
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with proper schema and indexes."""
    with get_db() as conn:
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    username TEXT,
                    phone TEXT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 1)''')
        
        # Scan history table with enhanced schema
        c.execute('''CREATE TABLE IF NOT EXISTS scan_history
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    email_subject TEXT,
                    email_body TEXT,
                    features TEXT,
                    prediction INTEGER,
                    confidence FLOAT,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_feedback INTEGER DEFAULT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')
        
        # Create indexes for performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_scan_history_user_id ON scan_history(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_scan_history_scan_time ON scan_history(scan_time DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_scan_history_prediction ON scan_history(prediction)')
        
        conn.commit()
        app.logger.info('Database initialized successfully')

# User model
class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if user:
            return User(id=user['id'], email=user['email'])
    return None

# Load ML model
def load_model():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "phishing_model.pkl")
    SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")
    
    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        return model, scaler
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return None, None

model, scaler = load_model()

@app.route('/', methods=['GET', 'POST'])
def home():
    # Normalize any POST hitting root to login page
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Login endpoint with rate limiting."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        if not email or not password:
            flash('Email and password are required', 'danger')
            return render_template('login.html')

        try:
            with get_db() as conn:
                c = conn.cursor()
                c.execute("SELECT id, email, password, is_active FROM users WHERE email = ?", (email,))
                user = c.fetchone()

            if user and user['is_active'] and check_password_hash(user['password'], password):
                user_obj = User(id=user['id'], email=user['email'])
                login_user(user_obj)
                
                # Update last login
                with get_db() as conn:
                    c = conn.cursor()
                    c.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                             (datetime.utcnow(), user['id']))
                    conn.commit()
                
                app.logger.info(f'User logged in: {email}')
                return redirect(url_for('dashboard'), code=303)
            elif user and not user['is_active']:
                flash('Account is deactivated. Please contact support.', 'danger')
            else:
                flash('Invalid email or password', 'danger')
                app.logger.warning(f'Failed login attempt for: {email}')
        except Exception as e:
            app.logger.error(f'Login error: {str(e)}')
            flash('An error occurred. Please try again.', 'danger')

    return render_template('login.html')

def validate_password(password):
    """Validate password strength.
    
    Requirements:
    - At least 8 characters
    - Contains uppercase and lowercase
    - Contains at least one number
    - Contains at least one special character
    - Not in common passwords list
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Check against common passwords
    common_passwords = ['password', '12345678', 'qwerty', 'admin', 'letmein', 'welcome']
    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password."
    
    return True, "Valid"

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    """Registration endpoint with rate limiting and password validation."""
    if request.method == 'POST':
        try:
            # Accept JSON or form-encoded
            if request.is_json:
                data = request.get_json(silent=True) or {}
            else:
                data = request.form.to_dict() if request.form else {}

            # Map inputs
            name = data.get('name') or data.get('full_name') or (
                (data.get('firstName') or data.get('first_name') or '') + ' ' + (data.get('lastName') or data.get('last_name') or '')
            ).strip()
            username = data.get('username')
            phone = data.get('phone')
            email = (data.get('email') or '').strip().lower()
            raw_password = data.get('password')

            if not all([email, raw_password, username, phone]):
                error_msg = 'Missing required fields'
                if request.is_json:
                    return jsonify({'success': False, 'error': error_msg}), 400
                flash(error_msg, 'danger')
                return render_template('register.html')
            
            # Validate email format
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.match(email):
                error_msg = 'Invalid email format'
                if request.is_json:
                    return jsonify({'success': False, 'error': error_msg}), 400
                flash(error_msg, 'danger')
                return render_template('register.html')
            
            # Validate password strength
            is_valid, message = validate_password(raw_password)
            if not is_valid:
                if request.is_json:
                    return jsonify({'success': False, 'error': message}), 400
                flash(message, 'danger')
                return render_template('register.html')

            password = generate_password_hash(raw_password)

            with get_db() as conn:
                c = conn.cursor()
                c.execute('SELECT id FROM users WHERE email = ?', (email,))
                if c.fetchone():
                    error_msg = 'Email already registered'
                    if request.is_json:
                        return jsonify({'success': False, 'error': error_msg}), 409
                    flash(error_msg, 'danger')
                    return render_template('register.html')

                c.execute('''
                    INSERT INTO users (name, username, phone, email, password)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, username, phone, email, password))
                user_id = c.lastrowid
                conn.commit()
            
            app.logger.info(f'New user registered: {email}')

            # If this was a normal form submission (not JSON), log in immediately and redirect to dashboard
            if not request.is_json:
                user_obj = User(id=user_id, email=email)
                login_user(user_obj)
                flash('Registration successful! Welcome to King-Phisher.', 'success')
                return redirect(url_for('dashboard'), code=303)

            return jsonify({'success': True}), 201
        except Exception as e:
            app.logger.error(f'Registration error: {str(e)}')
            error_msg = 'An error occurred during registration'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 500
            flash(error_msg, 'danger')
            return render_template('register.html')

    return render_template('register.html')

# Legacy static paths -> redirect to Flask routes (handles cached links like /register.html)
@app.route('/login.html')
def legacy_login_html():
    return redirect(url_for('login'), code=301)

@app.route('/register.html')
def legacy_register_html():
    return redirect(url_for('register'), code=301)

@app.route('/dashboard.html')
def legacy_dashboard_html():
    return redirect(url_for('dashboard'), code=301)

@app.route('/scan.html')
def legacy_scan_html():
    return redirect(url_for('scan'), code=301)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Dashboard with scan history and model metrics."""
    # If a POST sneaks in (e.g., from a cached form submit), normalize to GET
    if request.method == 'POST':
        # 303 to force GET
        return redirect(url_for('dashboard'), code=303)
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''SELECT email_subject, prediction, confidence, scan_time 
                     FROM scan_history WHERE user_id = ? ORDER BY scan_time DESC LIMIT 10''', 
                  (current_user.id,))
        rows = c.fetchall()

    # Convert rows to plain dicts for template simplicity
    history = [
        {
            'email_subject': row['email_subject'],
            'prediction': row['prediction'],
            'confidence': row['confidence'],
            'scan_time': row['scan_time'],
        }
        for row in rows
    ]
    phishing_count = sum(1 for r in history if int(r.get('prediction') or 0) == 1)
    
    # Load model metrics
    model_metrics = {}
    metrics_path = os.path.join(os.path.dirname(__file__), 'model_metrics.json')
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r') as f:
                model_metrics = json.load(f)
        except Exception as e:
            app.logger.warning(f'Could not load model metrics: {str(e)}')

    return render_template(
        'dashboard_enhanced.html',
        email=current_user.email,
        scan_history=history,
        phishing_count=phishing_count,
        model_metrics=model_metrics
    )

@app.route('/scan', methods=['GET', 'POST'])
@login_required
def scan():
    if request.method == 'POST':
        # Collect advanced features expected by the trained model
        expected_cols = [
            'num_words', 'num_unique_words', 'num_stopwords', 'num_links',
            'num_unique_domains', 'num_email_addresses', 'num_spelling_errors', 'num_urgent_keywords'
        ]

        # Read values from form (either from user or from some auto-extractor in future)
        form_vals = {}
        for col in expected_cols:
            form_vals[col] = request.form.get(col)

        # Backwards-compat: If advanced fields are not provided, fall back to old 4-field UI but show clear error
        if not all(form_vals.values()):
            flash('Scan failed: This model was trained on 8 features. Please fill all advanced fields under "Advanced Features".', 'danger')
            return redirect(url_for('scan'))

        try:
            if model is None or scaler is None:
                raise RuntimeError('Model or scaler not loaded. Please ensure model files exist.')

            # Cast to numeric in the correct order
            row = []
            for col in expected_cols:
                v = form_vals[col]
                # most are counts; allow float to be safe then cast to float
                row.append(float(v))

            input_df = pd.DataFrame([row], columns=expected_cols)
            input_scaled = scaler.transform(input_df)
            prediction = model.predict(input_scaled)[0]
            # Handle classifiers that may or may not support predict_proba
            confidence = 0.5
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(input_scaled)[0]
                # Assume class 1 is phishing
                confidence = float(proba[1])

            with get_db() as conn:
                c = conn.cursor()
                c.execute('''INSERT INTO scan_history 
                            (user_id, email_subject, prediction, confidence)
                            VALUES (?, ?, ?, ?)''',
                         (current_user.id, "Manual Scan", int(prediction), float(confidence)))
                conn.commit()

            result = "Phishing Detected" if prediction else "Email is Safe"
            flash(f"Scan Result: {result} (Confidence: {confidence:.2%})", 
                  'danger' if prediction else 'success')

        except Exception as e:
            flash(f"Scan failed: {str(e)}", 'danger')

        return redirect(url_for('scan'))

    # Expose a flag to the template so the UI can indicate model availability (optional)
    return render_template('scan_enhanced.html', model_loaded=(model is not None and scaler is not None))

@app.post('/api/scan-email')
@login_required
def api_scan_email():
    """API endpoint for AJAX email scanning.
    
    Body: JSON with 8 feature values
    Returns: { success: bool, prediction: int, confidence: float, result: str }
    """
    try:
        data = request.get_json(silent=True) or {}
        
        # Expected features
        expected_cols = [
            'num_words', 'num_unique_words', 'num_stopwords', 'num_links',
            'num_unique_domains', 'num_email_addresses', 'num_spelling_errors', 'num_urgent_keywords'
        ]
        
        # Validate all features are present
        missing = [col for col in expected_cols if col not in data]
        if missing:
            return jsonify({
                'success': False,
                'error': f'Missing required features: {", ".join(missing)}'
            }), 400
        
        # Validate model is loaded
        if model is None or scaler is None:
            return jsonify({
                'success': False,
                'error': 'Model not loaded. Please contact administrator.'
            }), 500
        
        # Extract and validate feature values
        try:
            row = [float(data[col]) for col in expected_cols]
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': f'Invalid feature value: {str(e)}'
            }), 400
        
        # Prepare input for model
        input_df = pd.DataFrame([row], columns=expected_cols)
        input_scaled = scaler.transform(input_df)
        
        # Make prediction
        prediction = int(model.predict(input_scaled)[0])
        confidence = 0.5
        
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(input_scaled)[0]
            confidence = float(proba[1])
        
        # Save to scan history
        email_subject = data.get('email_subject', 'AJAX Scan')
        email_body = data.get('email_body', '')
        
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO scan_history 
                        (user_id, email_subject, email_body, features, prediction, confidence)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (current_user.id, email_subject, email_body, 
                      json.dumps(data), int(prediction), float(confidence)))
            conn.commit()
        
        result = "Phishing Detected" if prediction else "Email is Safe"
        severity = "danger" if prediction else "success"
        
        app.logger.info(f'AJAX scan by {current_user.email}: {result} (confidence: {confidence:.2%})')
        
        return jsonify({
            'success': True,
            'prediction': prediction,
            'confidence': confidence,
            'result': result,
            'severity': severity,
            'message': f'{result} with {confidence:.1%} confidence'
        })
        
    except Exception as e:
        app.logger.error(f'AJAX scan error: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Scan failed: {str(e)}'
        }), 500

@app.get('/api/scan-stats')
@login_required
def api_scan_stats():
    """Get user's scan statistics for dashboard charts.
    
    Returns: { success: bool, stats: {...} }
    """
    try:
        with get_db() as conn:
            c = conn.cursor()
            
            # Get all scans for current user
            c.execute('''SELECT prediction, confidence, scan_time, email_subject
                        FROM scan_history 
                        WHERE user_id = ? 
                        ORDER BY scan_time DESC 
                        LIMIT 100''', (current_user.id,))
            scans = c.fetchall()
        
        if not scans:
            return jsonify({
                'success': True,
                'stats': {
                    'total_scans': 0,
                    'phishing_count': 0,
                    'safe_count': 0,
                    'avg_confidence': 0,
                    'recent_scans': []
                }
            })
        
        # Calculate statistics
        total_scans = len(scans)
        phishing_count = sum(1 for s in scans if s['prediction'] == 1)
        safe_count = total_scans - phishing_count
        avg_confidence = sum(s['confidence'] or 0.5 for s in scans) / total_scans
        
        # Prepare recent scans for chart
        recent_scans = []
        for scan in scans[:20]:  # Last 20 scans
            recent_scans.append({
                'time': scan['scan_time'],
                'prediction': scan['prediction'],
                'confidence': scan['confidence'],
                'subject': scan['email_subject']
            })
        
        # Group by date for timeline
        from collections import defaultdict
        daily_stats = defaultdict(lambda: {'safe': 0, 'phishing': 0})
        
        for scan in scans:
            date = scan['scan_time'][:10] if scan['scan_time'] else 'unknown'
            if scan['prediction'] == 1:
                daily_stats[date]['phishing'] += 1
            else:
                daily_stats[date]['safe'] += 1
        
        timeline = [
            {'date': date, 'safe': stats['safe'], 'phishing': stats['phishing']}
            for date, stats in sorted(daily_stats.items())[-14:]  # Last 14 days
        ]
        
        return jsonify({
            'success': True,
            'stats': {
                'total_scans': total_scans,
                'phishing_count': phishing_count,
                'safe_count': safe_count,
                'avg_confidence': round(avg_confidence, 4),
                'phishing_rate': round(phishing_count / total_scans * 100, 1) if total_scans > 0 else 0,
                'recent_scans': recent_scans,
                'timeline': timeline
            }
        })
        
    except Exception as e:
        app.logger.error(f'Stats API error: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.get('/api/domain-age')
def api_domain_age():
    """Compute domain age in days from a URL or domain string.
    Query params:
      - url: full URL (preferred)
      - domain: domain/hostname
    Returns: { success: bool, domain: str, created_at: str|null, age_days: int|null, error?: str }
    """
    raw_url = (request.args.get('url') or '').strip()
    raw_domain = (request.args.get('domain') or '').strip()

    # Extract domain using tldextract to be robust
    host = ''
    target = raw_url or raw_domain
    if not target:
        return jsonify({ 'success': False, 'error': 'Missing url or domain parameter' }), 400

    try:
        if raw_url:
            # Clean any surrounding spaces or quotes
            target = raw_url.strip().strip('"\'')
        ext = tldextract.extract(target)
        if not ext.suffix:
            # Not a valid domain
            return jsonify({ 'success': False, 'error': 'Invalid domain/URL' }), 400
        host = '.'.join(p for p in [ext.domain, ext.suffix] if p)
    except Exception as e:
        return jsonify({ 'success': False, 'error': f'Parse error: {str(e)}' }), 400

    if whois is None:
        return jsonify({ 'success': False, 'domain': host, 'error': 'WHOIS module not available on server' }), 500

    try:
        w = whois.whois(host)
        created = w.creation_date
        # python-whois may return a list of datetimes
        if isinstance(created, list):
            created = created[0] if created else None
        if created is None:
            return jsonify({ 'success': True, 'domain': host, 'created_at': None, 'age_days': None })
        if not isinstance(created, datetime):
            # Try to parse string
            try:
                created = datetime.fromisoformat(str(created))
            except Exception:
                created = None
        if created is None:
            return jsonify({ 'success': True, 'domain': host, 'created_at': None, 'age_days': None })
        age_days = (datetime.utcnow() - created.replace(tzinfo=None)).days
        return jsonify({ 'success': True, 'domain': host, 'created_at': created.isoformat(), 'age_days': int(age_days) })
    except Exception as e:
        return jsonify({ 'success': False, 'domain': host, 'error': str(e) }), 500

@app.post('/api/extract-email-features')
def api_extract_email_features():
    """Extract the 8 features expected by the model from raw email text.
    Body: JSON { text: str }
    Returns: { success: bool, features: {...} }
    """
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'success': False, 'error': 'Missing text'}), 400

    try:
        # Normalize
        text_l = text.lower()

        # URLs
        url_pattern = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE)
        urls = url_pattern.findall(text_l)
        num_links = len(urls)
        unique_domains = set()
        for u in urls:
            try:
                ext = tldextract.extract(u)
                if ext.suffix:
                    unique_domains.add('.'.join(p for p in [ext.domain, ext.suffix] if p))
            except Exception:
                pass
        num_unique_domains = len(unique_domains)

        # Emails
        email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        emails = email_pattern.findall(text)
        num_email_addresses = len(emails)

        # Words
        words = re.findall(r"[A-Za-z']+", text_l)
        num_words = len(words)
        num_unique_words = len(set(words))
        num_stopwords = sum(1 for w in words if w in STOPWORDS)

        # Spelling errors (optional)
        num_spelling_errors = 0
        if SpellChecker is not None and words:
            try:
                sp = SpellChecker()
                # Limit to a reasonable subset to avoid long processing
                candidates = [w for w in set(words) if len(w) > 2 and w.isalpha()]
                unknown = sp.unknown(candidates)
                # Approximate count proportional to frequency
                freq = {w: 0 for w in unknown}
                for w in words:
                    if w in freq:
                        freq[w] += 1
                num_spelling_errors = sum(freq.values())
            except Exception:
                num_spelling_errors = 0

        # Urgent keywords occurrences
        num_urgent_keywords = 0
        for kw in URGENT_KEYWORDS:
            num_urgent_keywords += len(re.findall(re.escape(kw), text_l))

        features = {
            'num_words': num_words,
            'num_unique_words': num_unique_words,
            'num_stopwords': num_stopwords,
            'num_links': num_links,
            'num_unique_domains': num_unique_domains,
            'num_email_addresses': num_email_addresses,
            'num_spelling_errors': num_spelling_errors,
            'num_urgent_keywords': num_urgent_keywords,
        }
        return jsonify({'success': True, 'features': features})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# PHASE 5: ADVANCED FEATURES
# ============================================================================

@app.route('/bulk-scan')
@login_required
def bulk_scan_page():
    """Bulk scanning page."""
    return render_template('bulk_scan.html')

@app.post('/api/bulk-scan')
@login_required
def api_bulk_scan():
    """Bulk email scanning from CSV upload.
    
    Expects CSV with 'email_text' column or individual feature columns.
    Returns streaming JSON responses for progress tracking.
    """
    import csv
    import io
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'error': 'File must be CSV'}), 400
    
    try:
        # Read CSV
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        rows = list(reader)
        total = len(rows)
        
        def generate():
            """Stream progress updates."""
            for i, row in enumerate(rows):
                try:
                    # Send progress
                    yield json.dumps({'type': 'progress', 'current': i+1, 'total': total}) + '\n'
                    
                    # Extract features from email_text if present
                    if 'email_text' in row:
                        # Use feature extraction API logic
                        text = row['email_text']
                        # Extract features (simplified version)
                        words = re.findall(r"[A-Za-z']+", text.lower())
                        features = {
                            'num_words': len(words),
                            'num_unique_words': len(set(words)),
                            'num_stopwords': sum(1 for w in words if w in STOPWORDS),
                            'num_links': len(re.findall(r"https?://", text)),
                            'num_unique_domains': 0,  # Simplified
                            'num_email_addresses': len(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)),
                            'num_spelling_errors': 0,  # Simplified
                            'num_urgent_keywords': sum(1 for kw in URGENT_KEYWORDS if kw in text.lower())
                        }
                    else:
                        # Use provided features
                        features = {k: float(row.get(k, 0)) for k in [
                            'num_words', 'num_unique_words', 'num_stopwords', 'num_links',
                            'num_unique_domains', 'num_email_addresses', 'num_spelling_errors', 'num_urgent_keywords'
                        ]}
                    
                    # Make prediction
                    if model and scaler:
                        row_data = [features[k] for k in [
                            'num_words', 'num_unique_words', 'num_stopwords', 'num_links',
                            'num_unique_domains', 'num_email_addresses', 'num_spelling_errors', 'num_urgent_keywords'
                        ]]
                        input_df = pd.DataFrame([row_data], columns=list(features.keys()))
                        input_scaled = scaler.transform(input_df)
                        prediction = int(model.predict(input_scaled)[0])
                        confidence = float(model.predict_proba(input_scaled)[0][1]) if hasattr(model, 'predict_proba') else 0.5
                    else:
                        prediction = 0
                        confidence = 0.5
                    
                    # Send result
                    result = {
                        'type': 'result',
                        'index': i,
                        'prediction': prediction,
                        'confidence': confidence,
                        'features': features,
                        'email_preview': row.get('email_text', '')[:100] if 'email_text' in row else 'N/A'
                    }
                    yield json.dumps(result) + '\n'
                    
                except Exception as e:
                    app.logger.error(f'Bulk scan error on row {i}: {str(e)}')
                    continue
            
            # Send completion
            yield json.dumps({'type': 'complete', 'total': total}) + '\n'
        
        return app.response_class(generate(), mimetype='application/x-ndjson')
        
    except Exception as e:
        app.logger.error(f'Bulk scan upload error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post('/api/export-pdf')
@login_required
def api_export_pdf():
    """Export scan results to PDF report."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.units import inch
        from io import BytesIO
        from datetime import datetime
        
        data = request.get_json(silent=True) or {}
        results = data.get('results', [])
        
        if not results:
            return jsonify({'success': False, 'error': 'No results to export'}), 400
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30
        )
        elements.append(Paragraph('🛡️ King-Phisher Scan Report', title_style))
        elements.append(Paragraph(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))
        elements.append(Paragraph(f'User: {current_user.email}', styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Summary
        total = len(results)
        phishing = sum(1 for r in results if r.get('prediction') == 1)
        safe = total - phishing
        avg_conf = sum(r.get('confidence', 0) for r in results) / total if total > 0 else 0
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Scanned', str(total)],
            ['Safe Emails', str(safe)],
            ['Phishing Detected', str(phishing)],
            ['Phishing Rate', f'{(phishing/total*100):.1f}%' if total > 0 else '0%'],
            ['Avg Confidence', f'{(avg_conf*100):.1f}%']
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Results Table
        elements.append(Paragraph('Detailed Results', styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        results_data = [['#', 'Preview', 'Result', 'Confidence']]
        for i, r in enumerate(results[:50]):  # Limit to 50 for PDF
            preview = (r.get('email_preview', 'N/A')[:50] + '...') if len(r.get('email_preview', '')) > 50 else r.get('email_preview', 'N/A')
            results_data.append([
                str(i+1),
                preview,
                'Phishing' if r.get('prediction') == 1 else 'Safe',
                f"{(r.get('confidence', 0)*100):.1f}%"
            ])
        
        results_table = Table(results_data, colWidths=[0.5*inch, 3.5*inch, 1*inch, 1*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        elements.append(results_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'phishing_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    except Exception as e:
        app.logger.error(f'PDF export error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post('/api/analyze-headers')
@login_required
def api_analyze_headers():
    """Analyze email headers for SPF, DKIM, DMARC validation.
    
    Body: { headers: str } - Raw email headers
    Returns: { success: bool, analysis: {...} }
    """
    try:
        import dns.resolver
        from email import message_from_string
        
        data = request.get_json(silent=True) or {}
        headers_text = data.get('headers', '')
        
        if not headers_text:
            return jsonify({'success': False, 'error': 'No headers provided'}), 400
        
        # Parse headers
        msg = message_from_string(headers_text)
        
        analysis = {
            'spf': 'Unknown',
            'dkim': 'Unknown',
            'dmarc': 'Unknown',
            'from_domain': None,
            'return_path': None,
            'received_spf': None,
            'authentication_results': None
        }
        
        # Extract key headers
        from_header = msg.get('From', '')
        if '@' in from_header:
            domain = from_header.split('@')[-1].strip('>')
            analysis['from_domain'] = domain
            
            # Check DMARC record
            try:
                dmarc_domain = f'_dmarc.{domain}'
                answers = dns.resolver.resolve(dmarc_domain, 'TXT')
                for rdata in answers:
                    txt = str(rdata).strip('"')
                    if txt.startswith('v=DMARC1'):
                        analysis['dmarc'] = 'Pass - Record Found'
                        break
            except:
                analysis['dmarc'] = 'Fail - No Record'
        
        analysis['return_path'] = msg.get('Return-Path', 'Not found')
        analysis['received_spf'] = msg.get('Received-SPF', 'Not found')
        analysis['authentication_results'] = msg.get('Authentication-Results', 'Not found')
        
        # Simple SPF check from headers
        if 'pass' in analysis['received_spf'].lower():
            analysis['spf'] = 'Pass'
        elif 'fail' in analysis['received_spf'].lower():
            analysis['spf'] = 'Fail'
        
        # Simple DKIM check from headers
        auth_results = analysis['authentication_results'].lower()
        if 'dkim=pass' in auth_results:
            analysis['dkim'] = 'Pass'
        elif 'dkim=fail' in auth_results:
            analysis['dkim'] = 'Fail'
        
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        app.logger.error(f'Header analysis error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post('/api/check-url-reputation')
@login_required
def api_check_url_reputation():
    """Check URL reputation using VirusTotal API.
    
    Body: { url: str }
    Returns: { success: bool, reputation: {...} }
    """
    try:
        import requests
        import hashlib
        import base64
        
        data = request.get_json(silent=True) or {}
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        # Get API key from environment
        vt_api_key = os.getenv('VIRUSTOTAL_API_KEY')
        
        if not vt_api_key:
            return jsonify({
                'success': False,
                'error': 'VirusTotal API key not configured. Set VIRUSTOTAL_API_KEY in .env file.'
            }), 503
        
        # Encode URL for VirusTotal
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip('=')
        
        # Query VirusTotal API
        headers = {'x-apikey': vt_api_key}
        response = requests.get(
            f'https://www.virustotal.com/api/v3/urls/{url_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 404:
            # URL not in database, submit for scanning
            scan_response = requests.post(
                'https://www.virustotal.com/api/v3/urls',
                headers=headers,
                data={'url': url},
                timeout=10
            )
            return jsonify({
                'success': True,
                'reputation': {
                    'status': 'submitted',
                    'message': 'URL submitted for scanning. Check back in a few minutes.'
                }
            })
        
        response.raise_for_status()
        result = response.json()
        
        # Extract reputation data
        stats = result.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
        reputation = {
            'malicious': stats.get('malicious', 0),
            'suspicious': stats.get('suspicious', 0),
            'harmless': stats.get('harmless', 0),
            'undetected': stats.get('undetected', 0),
            'total_scans': sum(stats.values()),
            'reputation_score': 'Safe' if stats.get('malicious', 0) == 0 else 'Malicious',
            'last_analysis_date': result.get('data', {}).get('attributes', {}).get('last_analysis_date')
        }
        
        return jsonify({'success': True, 'reputation': reputation})
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f'VirusTotal API error: {str(e)}')
        return jsonify({'success': False, 'error': f'API request failed: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f'URL reputation check error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post('/api/submit-feedback')
@login_required
def api_submit_feedback():
    """Submit user feedback for continuous learning.
    
    Body: { scan_id: int, is_correct: bool, actual_label: int }
    Returns: { success: bool }
    """
    try:
        data = request.get_json(silent=True) or {}
        scan_id = data.get('scan_id')
        is_correct = data.get('is_correct')
        actual_label = data.get('actual_label')  # 0 = safe, 1 = phishing
        
        if scan_id is None:
            return jsonify({'success': False, 'error': 'Missing scan_id'}), 400
        
        with get_db() as conn:
            c = conn.cursor()
            
            # Update feedback
            c.execute('''UPDATE scan_history 
                        SET user_feedback = ? 
                        WHERE id = ? AND user_id = ?''',
                     (actual_label, scan_id, current_user.id))
            conn.commit()
            
            if c.rowcount == 0:
                return jsonify({'success': False, 'error': 'Scan not found'}), 404
        
        app.logger.info(f'Feedback submitted by {current_user.email} for scan {scan_id}: correct={is_correct}, actual={actual_label}')
        
        return jsonify({'success': True, 'message': 'Feedback recorded. Thank you!'})
        
    except Exception as e:
        app.logger.error(f'Feedback submission error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.get('/api/search-scans')
@login_required
def api_search_scans():
    """Search and filter scan history.
    
    Query params: q (search), prediction (0/1), min_confidence, max_confidence, date_from, date_to
    Returns: { success: bool, results: [...] }
    """
    try:
        query = request.args.get('q', '').strip()
        prediction = request.args.get('prediction')
        min_conf = request.args.get('min_confidence', type=float)
        max_conf = request.args.get('max_confidence', type=float)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        with get_db() as conn:
            c = conn.cursor()
            
            # Build query
            sql = '''SELECT id, email_subject, email_body, prediction, confidence, scan_time, user_feedback
                    FROM scan_history 
                    WHERE user_id = ?'''
            params = [current_user.id]
            
            if query:
                sql += ' AND (email_subject LIKE ? OR email_body LIKE ?)'
                params.extend([f'%{query}%', f'%{query}%'])
            
            if prediction is not None:
                sql += ' AND prediction = ?'
                params.append(int(prediction))
            
            if min_conf is not None:
                sql += ' AND confidence >= ?'
                params.append(min_conf)
            
            if max_conf is not None:
                sql += ' AND confidence <= ?'
                params.append(max_conf)
            
            if date_from:
                sql += ' AND scan_time >= ?'
                params.append(date_from)
            
            if date_to:
                sql += ' AND scan_time <= ?'
                params.append(date_to)
            
            sql += ' ORDER BY scan_time DESC LIMIT 100'
            
            c.execute(sql, params)
            rows = c.fetchall()
        
        results = [
            {
                'id': row['id'],
                'email_subject': row['email_subject'],
                'email_body': row['email_body'][:200] if row['email_body'] else None,
                'prediction': row['prediction'],
                'confidence': row['confidence'],
                'scan_time': row['scan_time'],
                'user_feedback': row['user_feedback']
            }
            for row in rows
        ]
        
        return jsonify({'success': True, 'results': results, 'count': len(results)})
        
    except Exception as e:
        app.logger.error(f'Search error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.post('/api/toggle-dark-mode')
@login_required
def api_toggle_dark_mode():
    """Toggle dark mode preference for user.
    
    Body: { enabled: bool }
    Returns: { success: bool }
    """
    try:
        data = request.get_json(silent=True) or {}
        enabled = data.get('enabled', False)
        
        # Store in session or database
        # For now, just return success (frontend will handle via localStorage)
        
        app.logger.info(f'Dark mode toggled by {current_user.email}: {enabled}')
        
        return jsonify({'success': True, 'dark_mode': enabled})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

@app.errorhandler(405)
def method_not_allowed(e):
    # If a POST refresh lands on a page that only accepts GET, steer the user correctly
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'), code=303)
    except Exception:
        pass
    return redirect(url_for('login'), code=303)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
