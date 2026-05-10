"""
Alert generation system with rule-based detection
"""
from typing import Dict, List, Optional
from datetime import datetime
import config


class AlertSystem:
    """Generates security alerts based on predefined rules"""
    
    def __init__(self):
        self.alert_rules = config.ALERT_RULES
        self.object_history = {}  # Track object appearances
        self.location_activity = {}  # Track activity by location
    
    def evaluate_frame(self, frame_data: Dict, ai_analysis: Dict) -> List[Dict]:
        """Evaluate frame against all alert rules"""
        alerts = []
        timestamp = datetime.strptime(frame_data['timestamp'], "%Y-%m-%d %H:%M:%S")
        
        # Rule 1: Midnight activity detection
        if self._check_midnight_activity(timestamp):
            alerts.append({
                "alert_type": "midnight_activity",
                "severity": "high",
                "description": f"Activity detected during restricted hours at {frame_data.get('location', 'unknown')}",
                "timestamp": frame_data['timestamp'],
                "rule": "midnight_activity"
            })
        
        # Rule 2: Suspicious behavior keywords
        suspicious_alert = self._check_suspicious_behavior(frame_data['description'])
        if suspicious_alert:
            alerts.append(suspicious_alert)
        
        # Rule 3: Vehicle repetition tracking
        vehicle_alerts = self._check_vehicle_repetition(frame_data)
        alerts.extend(vehicle_alerts)
        
        # Rule 4: Restricted zone access
        if self._check_restricted_zone(frame_data.get('location', '')):
            alerts.append({
                "alert_type": "restricted_zone",
                "severity": "medium",
                "description": f"Activity in restricted zone: {frame_data.get('location', 'unknown')}",
                "timestamp": frame_data['timestamp'],
                "rule": "restricted_zone"
            })
        
        # Rule 5: AI-based security assessment
        if ai_analysis.get('security_level') in ['high', 'critical']:
            alerts.append({
                "alert_type": "ai_security_assessment",
                "severity": ai_analysis.get('security_level', 'medium'),
                "description": ai_analysis.get('detailed_analysis', 'Security concern detected'),
                "timestamp": frame_data['timestamp'],
                "rule": "ai_analysis"
            })
        
        return alerts
    
    def _check_midnight_activity(self, timestamp: datetime) -> bool:
        """Check if activity occurs during restricted hours"""
        hour = timestamp.hour
        rules = self.alert_rules['midnight_activity']
        return hour >= rules['start_hour'] or hour < rules['end_hour']
    
    def _check_suspicious_behavior(self, description: str) -> Optional[Dict]:
        """Check for suspicious keywords in description"""
        description_lower = description.lower()
        keywords = self.alert_rules['suspicious_behavior']['keywords']
        
        for keyword in keywords:
            if keyword in description_lower:
                return {
                    "alert_type": "suspicious_behavior",
                    "severity": "high",
                    "description": f"Suspicious activity detected: {keyword}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "rule": "suspicious_behavior",
                    "keyword": keyword
                }
        return None
    
    def _check_vehicle_repetition(self, frame_data: Dict) -> List[Dict]:
        """Track and alert on repeated vehicle appearances"""
        alerts = []
        objects = frame_data.get('objects', [])
        
        for obj in objects:
            if obj.get('type') == 'vehicle':
                identifier = obj.get('identifier', obj.get('details', {}).get('model', 'unknown'))
                
                if identifier not in self.object_history:
                    self.object_history[identifier] = []
                
                self.object_history[identifier].append({
                    "timestamp": frame_data['timestamp'],
                    "location": frame_data.get('location', 'unknown')
                })
                
                # Check if threshold exceeded
                count = len(self.object_history[identifier])
                threshold = self.alert_rules['vehicle_repeat']['threshold']
                
                if count == threshold:
                    alerts.append({
                        "alert_type": "vehicle_repeat",
                        "severity": "medium",
                        "description": f"{identifier} detected {count} times today",
                        "timestamp": frame_data['timestamp'],
                        "rule": "vehicle_repeat",
                        "vehicle": identifier,
                        "occurrences": count
                    })
        
        return alerts
    
    def _check_restricted_zone(self, location: str) -> bool:
        """Check if location is a restricted zone"""
        restricted_zones = self.alert_rules['restricted_zone']['zones']
        return location in restricted_zones
    
    def format_alert(self, alert: Dict) -> str:
        """Format alert for display"""
        severity_emoji = {
            "low": "ℹ️",
            "medium": "⚠️",
            "high": "🚨",
            "critical": "🔴"
        }
        
        emoji = severity_emoji.get(alert['severity'], "⚠️")
        return f"{emoji} [{alert['severity'].upper()}] {alert['description']} (Time: {alert['timestamp']})"
    
    def get_alert_statistics(self) -> Dict:
        """Get statistics on generated alerts"""
        return {
            "tracked_vehicles": len(self.object_history),
            "vehicle_details": {
                vehicle: len(appearances)
                for vehicle, appearances in self.object_history.items()
            }
        }