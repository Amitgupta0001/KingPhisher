"""
Real-Time Threat Intelligence Integration for King-Phisher
Supports multiple threat intelligence sources
"""

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import hashlib


class ThreatIntelligence:
    """Aggregates threat intelligence from multiple sources."""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)
    
    def check_url(self, url: str) -> Dict:
        """
        Check URL against multiple threat intelligence sources.
        
        Returns:
            {
                'is_malicious': bool,
                'threat_score': float (0-100),
                'sources': {...},
                'details': {...}
            }
        """
        # Check cache first
        cache_key = hashlib.md5(url.encode()).hexdigest()
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached['timestamp'] < self.cache_ttl:
                return cached['data']
        
        results = {
            'is_malicious': False,
            'threat_score': 0,
            'sources': {},
            'details': {}
        }
        
        # Check multiple sources
        sources = [
            self._check_phishtank(url),
            self._check_urlhaus(url),
            self._check_google_safe_browsing(url),
            self._check_alienvault_otx(url)
        ]
        
        # Aggregate results
        malicious_count = 0
        total_score = 0
        
        for source_name, source_result in sources:
            if source_result:
                results['sources'][source_name] = source_result
                if source_result.get('is_malicious'):
                    malicious_count += 1
                total_score += source_result.get('score', 0)
        
        # Calculate final threat score
        if len(sources) > 0:
            results['threat_score'] = total_score / len(sources)
            results['is_malicious'] = malicious_count >= 2  # Consensus from 2+ sources
        
        # Cache result
        self.cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': results
        }
        
        return results
    
    def _check_phishtank(self, url: str) -> tuple:
        """Check URL against PhishTank database."""
        try:
            api_key = os.getenv('PHISHTANK_API_KEY')
            if not api_key:
                return ('phishtank', None)
            
            response = requests.post(
                'https://checkurl.phishtank.com/checkurl/',
                data={
                    'url': url,
                    'format': 'json',
                    'app_key': api_key
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    'is_malicious': data.get('results', {}).get('in_database', False),
                    'score': 100 if data.get('results', {}).get('in_database') else 0,
                    'verified': data.get('results', {}).get('verified', False)
                }
                return ('phishtank', result)
            
        except Exception as e:
            print(f"PhishTank error: {e}")
        
        return ('phishtank', None)
    
    def _check_urlhaus(self, url: str) -> tuple:
        """Check URL against URLhaus database."""
        try:
            response = requests.post(
                'https://urlhaus-api.abuse.ch/v1/url/',
                data={'url': url},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                is_malicious = data.get('query_status') == 'ok'
                
                result = {
                    'is_malicious': is_malicious,
                    'score': 100 if is_malicious else 0,
                    'threat_type': data.get('threat', 'unknown'),
                    'tags': data.get('tags', [])
                }
                return ('urlhaus', result)
            
        except Exception as e:
            print(f"URLhaus error: {e}")
        
        return ('urlhaus', None)
    
    def _check_google_safe_browsing(self, url: str) -> tuple:
        """Check URL against Google Safe Browsing API."""
        try:
            api_key = os.getenv('GOOGLE_SAFE_BROWSING_API_KEY')
            if not api_key:
                return ('google_safe_browsing', None)
            
            response = requests.post(
                f'https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}',
                json={
                    'client': {
                        'clientId': 'king-phisher',
                        'clientVersion': '1.0.0'
                    },
                    'threatInfo': {
                        'threatTypes': ['MALWARE', 'SOCIAL_ENGINEERING', 'UNWANTED_SOFTWARE'],
                        'platformTypes': ['ANY_PLATFORM'],
                        'threatEntryTypes': ['URL'],
                        'threatEntries': [{'url': url}]
                    }
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])
                is_malicious = len(matches) > 0
                
                result = {
                    'is_malicious': is_malicious,
                    'score': 100 if is_malicious else 0,
                    'threat_types': [m.get('threatType') for m in matches]
                }
                return ('google_safe_browsing', result)
            
        except Exception as e:
            print(f"Google Safe Browsing error: {e}")
        
        return ('google_safe_browsing', None)
    
    def _check_alienvault_otx(self, url: str) -> tuple:
        """Check URL against AlienVault OTX."""
        try:
            api_key = os.getenv('ALIENVAULT_OTX_API_KEY')
            if not api_key:
                return ('alienvault_otx', None)
            
            # Extract domain from URL
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            response = requests.get(
                f'https://otx.alienvault.com/api/v1/indicators/domain/{domain}/general',
                headers={'X-OTX-API-KEY': api_key},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                pulse_count = data.get('pulse_info', {}).get('count', 0)
                is_malicious = pulse_count > 0
                
                result = {
                    'is_malicious': is_malicious,
                    'score': min(pulse_count * 10, 100),
                    'pulse_count': pulse_count
                }
                return ('alienvault_otx', result)
            
        except Exception as e:
            print(f"AlienVault OTX error: {e}")
        
        return ('alienvault_otx', None)
    
    def check_ip(self, ip_address: str) -> Dict:
        """Check IP address reputation."""
        try:
            api_key = os.getenv('ABUSEIPDB_API_KEY')
            if not api_key:
                return {'error': 'AbuseIPDB API key not configured'}
            
            response = requests.get(
                'https://api.abuseipdb.com/api/v2/check',
                headers={'Key': api_key, 'Accept': 'application/json'},
                params={'ipAddress': ip_address, 'maxAgeInDays': 90},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json().get('data', {})
                return {
                    'is_malicious': data.get('abuseConfidenceScore', 0) > 50,
                    'abuse_score': data.get('abuseConfidenceScore', 0),
                    'total_reports': data.get('totalReports', 0),
                    'country': data.get('countryCode', 'Unknown')
                }
            
        except Exception as e:
            print(f"AbuseIPDB error: {e}")
        
        return {'error': str(e)}
    
    def get_domain_age(self, domain: str) -> Optional[int]:
        """Get domain age in days."""
        try:
            import whois
            w = whois.whois(domain)
            
            if w.creation_date:
                creation = w.creation_date
                if isinstance(creation, list):
                    creation = creation[0]
                
                age = (datetime.now() - creation).days
                return age
            
        except Exception as e:
            print(f"WHOIS error: {e}")
        
        return None


# Global instance
threat_intel = ThreatIntelligence()


def check_url_reputation(url: str) -> Dict:
    """
    Check URL reputation across multiple threat intelligence sources.
    
    Args:
        url: URL to check
    
    Returns:
        Aggregated threat intelligence data
    """
    return threat_intel.check_url(url)


def check_ip_reputation(ip: str) -> Dict:
    """
    Check IP address reputation.
    
    Args:
        ip: IP address to check
    
    Returns:
        IP reputation data
    """
    return threat_intel.check_ip(ip)
