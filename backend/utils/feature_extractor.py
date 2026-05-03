import re
import tldextract
from typing import Dict, List, Any

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

URL_SUSPICIOUS_KEYWORDS = {
    'login', 'verify', 'account', 'secure', 'update', 'banking', 'money', 'business', 'signin', 'support'
}

def extract_url_features(url: str) -> List[float]:
    """
    Extract features from a URL in the exact order required by the model.
    Order: [url_length, has_at, has_dash, has_https]
    """
    url_l = url.lower()
    
    # Check for suspicious keywords in URL
    suspicious_count = 0
    for kw in URL_SUSPICIOUS_KEYWORDS:
        if kw in url_l:
            suspicious_count += 1

    return [
        float(len(url)),
        float("@" in url),
        float("-" in url),
        float("https" in url),
        float(suspicious_count) # Extra data for heuristic
    ]

def extract_email_features(text: str) -> Dict[str, Any]:
    """
    Extract features from email text.
    Reused from old app.py logic.
    """
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

    # Urgent keywords
    num_urgent_keywords = 0
    for kw in URGENT_KEYWORDS:
        num_urgent_keywords += len(re.findall(re.escape(kw), text_l))

    # Spelling errors (Simplified: can use pyspellchecker if installed)
    num_spelling_errors = 0 

    return {
        'num_words': num_words,
        'num_unique_words': num_unique_words,
        'num_stopwords': num_stopwords,
        'num_links': num_links,
        'num_unique_domains': num_unique_domains,
        'num_email_addresses': num_email_addresses,
        'num_spelling_errors': num_spelling_errors,
        'num_urgent_keywords': num_urgent_keywords,
    }
