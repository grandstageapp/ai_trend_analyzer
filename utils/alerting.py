"""
Alerting system for critical issues and monitoring
"""
import logging
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from utils.health_checks import HealthStatus, HealthCheckResult
from utils.exceptions import AITrendsException

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertChannel(Enum):
    LOG = "log"
    EMAIL = "email"
    WEBHOOK = "webhook"
    FILE = "file"

@dataclass
class Alert:
    id: str
    title: str
    message: str
    severity: AlertSeverity
    source: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data

class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_handlers: Dict[AlertChannel, List[Callable]] = {
            AlertChannel.LOG: [self._log_handler],
            AlertChannel.FILE: [self._file_handler]
        }
        self.alert_thresholds = {
            'database_response_time': 5000,  # 5 seconds
            'cache_hit_rate': 50,  # 50%
            'memory_usage': 90,  # 90%
            'disk_usage': 90,  # 90%
            'error_rate': 10  # 10%
        }
        self.alert_cooldown = timedelta(minutes=15)  # Prevent alert spam
        self.last_alert_times: Dict[str, datetime] = {}
    
    def create_alert(self, title: str, message: str, severity: AlertSeverity, 
                    source: str, details: Optional[Dict[str, Any]] = None) -> Alert:
        """Create a new alert"""
        alert_id = f"{source}_{int(datetime.utcnow().timestamp())}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity,
            source=source,
            timestamp=datetime.utcnow(),
            details=details
        )
        
        # Check cooldown to prevent spam
        last_alert_key = f"{source}_{title}"
        if last_alert_key in self.last_alert_times:
            time_since_last = datetime.utcnow() - self.last_alert_times[last_alert_key]
            if time_since_last < self.alert_cooldown:
                logger.debug(f"Alert '{title}' suppressed due to cooldown")
                return alert
        
        self.active_alerts[alert_id] = alert
        self.last_alert_times[last_alert_key] = datetime.utcnow()
        
        # Send alert through configured channels
        self._send_alert(alert)
        
        logger.info(f"Alert created: {alert.title} ({alert.severity.value})")
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            self.active_alerts[alert_id].resolved_at = datetime.utcnow()
            
            logger.info(f"Alert resolved: {alert_id}")
            return True
        
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get all active alerts, optionally filtered by severity"""
        alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def cleanup_old_alerts(self, days: int = 7) -> int:
        """Clean up old resolved alerts"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        old_alerts = []
        
        for alert_id, alert in self.active_alerts.items():
            if alert.resolved and alert.resolved_at and alert.resolved_at < cutoff_time:
                old_alerts.append(alert_id)
        
        for alert_id in old_alerts:
            del self.active_alerts[alert_id]
        
        logger.info(f"Cleaned up {len(old_alerts)} old alerts")
        return len(old_alerts)
    
    def check_health_results(self, health_results: Dict[str, HealthCheckResult]):
        """Check health results and create alerts for issues"""
        for check_name, result in health_results.items():
            if result.status == HealthStatus.CRITICAL:
                self.create_alert(
                    title=f"Critical Health Check Failure: {check_name}",
                    message=result.message,
                    severity=AlertSeverity.CRITICAL,
                    source="health_check",
                    details={
                        'check_name': check_name,
                        'response_time_ms': result.response_time_ms,
                        'details': result.details
                    }
                )
            elif result.status == HealthStatus.WARNING:
                self.create_alert(
                    title=f"Health Check Warning: {check_name}",
                    message=result.message,
                    severity=AlertSeverity.MEDIUM,
                    source="health_check",
                    details={
                        'check_name': check_name,
                        'response_time_ms': result.response_time_ms,
                        'details': result.details
                    }
                )
    
    def check_performance_metrics(self, metrics: Dict[str, Any]):
        """Check performance metrics and create alerts for thresholds"""
        # Check database response times
        if 'database' in metrics and 'avg_response_time' in metrics['database']:
            response_time = metrics['database']['avg_response_time'] * 1000  # Convert to ms
            if response_time > self.alert_thresholds['database_response_time']:
                self.create_alert(
                    title="Database Response Time High",
                    message=f"Average response time: {response_time:.1f}ms",
                    severity=AlertSeverity.HIGH,
                    source="performance",
                    details={'response_time_ms': response_time}
                )
        
        # Check cache hit rate
        if 'cache' in metrics and 'hit_rate_percent' in metrics['cache']:
            hit_rate = metrics['cache']['hit_rate_percent']
            if hit_rate < self.alert_thresholds['cache_hit_rate']:
                self.create_alert(
                    title="Cache Hit Rate Low",
                    message=f"Cache hit rate: {hit_rate:.1f}%",
                    severity=AlertSeverity.MEDIUM,
                    source="performance",
                    details={'hit_rate_percent': hit_rate}
                )
    
    def _send_alert(self, alert: Alert):
        """Send alert through configured channels"""
        channels = self._get_channels_for_severity(alert.severity)
        
        for channel in channels:
            if channel in self.alert_handlers:
                for handler in self.alert_handlers[channel]:
                    try:
                        handler(alert)
                    except Exception as e:
                        logger.error(f"Alert handler failed for {channel}: {e}")
    
    def _get_channels_for_severity(self, severity: AlertSeverity) -> List[AlertChannel]:
        """Get appropriate channels based on alert severity"""
        if severity == AlertSeverity.CRITICAL:
            return [AlertChannel.LOG, AlertChannel.FILE]
        elif severity == AlertSeverity.HIGH:
            return [AlertChannel.LOG, AlertChannel.FILE]
        elif severity == AlertSeverity.MEDIUM:
            return [AlertChannel.LOG]
        else:
            return [AlertChannel.LOG]
    
    def _log_handler(self, alert: Alert):
        """Handle alert logging"""
        log_level = {
            AlertSeverity.LOW: logging.INFO,
            AlertSeverity.MEDIUM: logging.WARNING,
            AlertSeverity.HIGH: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }.get(alert.severity, logging.INFO)
        
        logger.log(log_level, f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}")
    
    def _file_handler(self, alert: Alert):
        """Handle alert file logging"""
        try:
            with open("alerts.log", "a") as f:
                alert_data = alert.to_dict()
                f.write(json.dumps(alert_data) + "\n")
        except Exception as e:
            logger.error(f"Failed to write alert to file: {e}")
    
    def add_alert_handler(self, channel: AlertChannel, handler: Callable[[Alert], None]):
        """Add a custom alert handler"""
        if channel not in self.alert_handlers:
            self.alert_handlers[channel] = []
        
        self.alert_handlers[channel].append(handler)
        logger.info(f"Added alert handler for {channel.value}")
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_alerts = [
            alert for alert in self.active_alerts.values()
            if alert.timestamp > cutoff_time
        ]
        
        by_severity = {}
        for severity in AlertSeverity:
            by_severity[severity.value] = len([
                alert for alert in recent_alerts 
                if alert.severity == severity
            ])
        
        by_source = {}
        for alert in recent_alerts:
            by_source[alert.source] = by_source.get(alert.source, 0) + 1
        
        return {
            'time_period_hours': hours,
            'total_alerts': len(recent_alerts),
            'active_alerts': len([a for a in recent_alerts if not a.resolved]),
            'by_severity': by_severity,
            'by_source': by_source,
            'most_recent': recent_alerts[0].to_dict() if recent_alerts else None
        }

# Global alert manager instance
alert_manager = AlertManager()