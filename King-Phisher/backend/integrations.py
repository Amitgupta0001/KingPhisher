"""
Communication Platform Integration for King-Phisher
Supports Slack, Discord, and Microsoft Teams
"""

import requests
import json
from datetime import datetime
from typing import Dict, Optional, List


class SlackIntegration:
    """Slack webhook integration for notifications."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_scan_alert(self, email_subject: str, prediction: int, confidence: float, user_email: str) -> bool:
        """Send scan result alert to Slack."""
        try:
            color = "#ef4444" if prediction == 1 else "#16a34a"
            result_text = "🚨 *Phishing Detected*" if prediction == 1 else "✅ *Email is Safe*"
            
            payload = {
                "attachments": [{
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "🛡️ King-Phisher Scan Alert"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": result_text
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Email Subject:*\n{email_subject[:100]}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Confidence:*\n{confidence*100:.1f}%"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Scanned By:*\n{user_email}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                }
                            ]
                        }
                    ]
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Slack notification error: {e}")
            return False
    
    def send_daily_report(self, stats: Dict) -> bool:
        """Send daily statistics report to Slack."""
        try:
            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📊 King-Phisher Daily Report"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Scans:*\n{stats.get('total_scans', 0)}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Phishing Detected:*\n{stats.get('phishing_count', 0)}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Safe Emails:*\n{stats.get('safe_count', 0)}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Avg Confidence:*\n{stats.get('avg_confidence', 0)*100:.1f}%"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Phishing Rate:* {stats.get('phishing_rate', 0):.1f}%"
                        }
                    }
                ]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Slack report error: {e}")
            return False


class DiscordIntegration:
    """Discord webhook integration for notifications."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_scan_alert(self, email_subject: str, prediction: int, confidence: float, user_email: str) -> bool:
        """Send scan result alert to Discord."""
        try:
            color = 0xef4444 if prediction == 1 else 0x16a34a
            result_text = "🚨 **Phishing Detected**" if prediction == 1 else "✅ **Email is Safe**"
            
            payload = {
                "embeds": [{
                    "title": "🛡️ King-Phisher Scan Alert",
                    "description": result_text,
                    "color": color,
                    "fields": [
                        {
                            "name": "Email Subject",
                            "value": email_subject[:100],
                            "inline": False
                        },
                        {
                            "name": "Confidence",
                            "value": f"{confidence*100:.1f}%",
                            "inline": True
                        },
                        {
                            "name": "Scanned By",
                            "value": user_email,
                            "inline": True
                        }
                    ],
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {
                        "text": "King-Phisher Security"
                    }
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            return response.status_code == 204
            
        except Exception as e:
            print(f"Discord notification error: {e}")
            return False
    
    def send_daily_report(self, stats: Dict) -> bool:
        """Send daily statistics report to Discord."""
        try:
            payload = {
                "embeds": [{
                    "title": "📊 King-Phisher Daily Report",
                    "color": 0x3b82f6,
                    "fields": [
                        {
                            "name": "Total Scans",
                            "value": str(stats.get('total_scans', 0)),
                            "inline": True
                        },
                        {
                            "name": "Phishing Detected",
                            "value": str(stats.get('phishing_count', 0)),
                            "inline": True
                        },
                        {
                            "name": "Safe Emails",
                            "value": str(stats.get('safe_count', 0)),
                            "inline": True
                        },
                        {
                            "name": "Avg Confidence",
                            "value": f"{stats.get('avg_confidence', 0)*100:.1f}%",
                            "inline": True
                        },
                        {
                            "name": "Phishing Rate",
                            "value": f"{stats.get('phishing_rate', 0):.1f}%",
                            "inline": True
                        }
                    ],
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {
                        "text": "King-Phisher Security"
                    }
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            return response.status_code == 204
            
        except Exception as e:
            print(f"Discord report error: {e}")
            return False


class TeamsIntegration:
    """Microsoft Teams webhook integration for notifications."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_scan_alert(self, email_subject: str, prediction: int, confidence: float, user_email: str) -> bool:
        """Send scan result alert to Microsoft Teams."""
        try:
            theme_color = "FF4444" if prediction == 1 else "16A34A"
            result_text = "🚨 Phishing Detected" if prediction == 1 else "✅ Email is Safe"
            
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": "King-Phisher Scan Alert",
                "themeColor": theme_color,
                "title": "🛡️ King-Phisher Scan Alert",
                "sections": [{
                    "activityTitle": result_text,
                    "facts": [
                        {
                            "name": "Email Subject:",
                            "value": email_subject[:100]
                        },
                        {
                            "name": "Confidence:",
                            "value": f"{confidence*100:.1f}%"
                        },
                        {
                            "name": "Scanned By:",
                            "value": user_email
                        },
                        {
                            "name": "Time:",
                            "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                    ]
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Teams notification error: {e}")
            return False


def send_notification(platform: str, webhook_url: str, notification_type: str, data: Dict) -> bool:
    """
    Send notification to specified platform.
    
    Args:
        platform: 'slack', 'discord', or 'teams'
        webhook_url: Webhook URL for the platform
        notification_type: 'scan_alert' or 'daily_report'
        data: Notification data
    
    Returns:
        bool: Success status
    """
    try:
        if platform == 'slack':
            integration = SlackIntegration(webhook_url)
        elif platform == 'discord':
            integration = DiscordIntegration(webhook_url)
        elif platform == 'teams':
            integration = TeamsIntegration(webhook_url)
        else:
            return False
        
        if notification_type == 'scan_alert':
            return integration.send_scan_alert(
                email_subject=data.get('email_subject', 'N/A'),
                prediction=data.get('prediction', 0),
                confidence=data.get('confidence', 0.5),
                user_email=data.get('user_email', 'Unknown')
            )
        elif notification_type == 'daily_report':
            return integration.send_daily_report(data)
        
        return False
        
    except Exception as e:
        print(f"Notification error: {e}")
        return False
