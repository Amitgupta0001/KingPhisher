from typing import Dict, Any, List

def explain_phishing(url: str, features: List[float]) -> str:
    """
    Provide a human-readable explanation for why a URL might be phishing.
    """
    reasons = []
    
    # Simple heuristic-based explanation for now
    if features[0] > 100:
        reasons.append("The URL is unusually long.")
    if features[1] == 1.0:
        reasons.append("The URL contains an '@' symbol, often used to redirect users.")
    if features[2] == 1.0:
        reasons.append("The URL contains hyphens, which can be used to mimic real domains.")
    if features[3] == 0.0:
        reasons.append("The site does not use HTTPS, which is suspicious for secure services.")
    
    if not reasons:
        return "Suspicious domain pattern detected by AI model."
    
    return " ".join(reasons)

def explain_email_phishing(features: Dict[str, Any]) -> str:
    """
    Provide a human-readable explanation for why an email might be phishing.
    """
    reasons = []
    
    if features['num_urgent_keywords'] > 0:
        reasons.append(f"Contains {features['num_urgent_keywords']} urgent keywords (e.g., 'verify', 'suspended').")
    if features['num_links'] > 5:
        reasons.append("Contains an unusually high number of links.")
    if features['num_unique_domains'] > 2:
        reasons.append("Contains links to multiple different domains.")
    
    if not reasons:
        return "Content pattern matches known phishing tactics."
    
    return " ".join(reasons)
