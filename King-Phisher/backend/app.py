from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
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
try:
    import whois  # python-whois package
except Exception:
    whois = None
try:
    from spellchecker import SpellChecker  # pyspellchecker
except Exception:
    SpellChecker = None

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
# Use a stable secret key so session cookies survive redirects and debug reloads
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    username TEXT,
                    phone TEXT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS scan_history
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    email_subject TEXT,
                    prediction INTEGER,
                    confidence FLOAT,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id))''')
        conn.commit()

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
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id, email, password FROM users WHERE email = ?", (email,))
            user = c.fetchone()

        if user and check_password_hash(user['password'], password):
            user_obj = User(id=user['id'], email=user['email'])
            login_user(user_obj)
            # 303 to force a GET on the next request
            return redirect(url_for('dashboard'), code=303)

        flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
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
                return jsonify({'success': False, 'error': 'Missing required fields'}), 400

            password = generate_password_hash(raw_password)

            with get_db() as conn:
                c = conn.cursor()
                c.execute('SELECT id FROM users WHERE email = ?', (email,))
                if c.fetchone():
                    return jsonify({'success': False, 'error': 'Email already registered'}), 409

                c.execute('''
                    INSERT INTO users (name, username, phone, email, password)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, username, phone, email, password))
                user_id = c.lastrowid
                conn.commit()

            # If this was a normal form submission (not JSON), log in immediately and redirect to dashboard
            if not request.is_json:
                user_obj = User(id=user_id, email=email)
                login_user(user_obj)
                return redirect(url_for('dashboard'), code=303)

            return jsonify({'success': True}), 201
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

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

    return render_template(
        'dashboard.html',
        email=current_user.email,
        scan_history=history,
        phishing_count=phishing_count,
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
    return render_template('scan.html', model_loaded=(model is not None and scaler is not None))

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
