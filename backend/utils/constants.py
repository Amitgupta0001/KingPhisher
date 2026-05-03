# Centralized constants for King Phisher AI

# Email Scanning Constants
MAX_EMAIL_TEXT_LENGTH = 50000

EMAIL_FEATURE_ORDER = [
    "num_words",
    "num_unique_words",
    "num_stopwords",
    "num_links",
    "num_unique_domains",
    "num_email_addresses",
    "num_spelling_errors",
    "num_urgent_keywords"
]

# URL Scanning Constants
URL_FEATURE_ORDER = [
    "url_length",
    "has_at",
    "has_dash",
    "has_https"
]
