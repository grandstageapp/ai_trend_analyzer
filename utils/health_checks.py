"""
Health check system for monitoring application status
"""
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from app import db
from models import Post, Author, Trend
from config import Config
from utils.exceptions import DatabaseException, ConfigurationException

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.config = Config()
        self.checks = {
            'database': self._check_database,
            'api_keys': self._check_api_keys,
            'disk_space': self._check_disk_space,
            'memory_usage': self._check_memory_usage,
            'recent_data': self._check_recent_data,
            'cache_system': self._check_cache_system,
            'background_tasks': self._check_background_tasks
        }
    
    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks and return results"""
        results = {}
        
        for check_name, check_func in self.checks.items():
            try:
                start_time = time.time()
                result = check_func()
                end_time = time.time()
                
                result.response_time_ms = (end_time - start_time) * 1000
                results[check_name] = result
                
            except Exception as e:
                logger.error(f"Health check '{check_name}' failed: {e}")
                results[check_name] = HealthCheckResult(
                    name=check_name,
                    status=HealthStatus.CRITICAL,
                    message=f"Check execution failed: {e}",
                    response_time_ms=None
                )
        
        return results
    
    def _check_database(self) -> HealthCheckResult:
        """Check database connectivity and basic operations"""
        try:
            # Test connection with a simple query
            result = db.session.execute(db.text("SELECT 1")).scalar()
            
            if result != 1:
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.CRITICAL,
                    message="Database query returned unexpected result"
                )
            
            # Check table existence
            tables = ['authors', 'posts', 'trends', 'engagement', 'trend_scores']
            for table in tables:
                try:
                    db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
                except Exception as e:
                    return HealthCheckResult(
                        name="database",
                        status=HealthStatus.CRITICAL,
                        message=f"Table '{table}' check failed: {e}"
                    )
            
            # Get basic stats
            author_count = db.session.execute(db.text("SELECT COUNT(*) FROM authors")).scalar()
            post_count = db.session.execute(db.text("SELECT COUNT(*) FROM posts")).scalar()
            trend_count = db.session.execute(db.text("SELECT COUNT(*) FROM trends")).scalar()
            
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connectivity and tables OK",
                details={
                    'authors': author_count,
                    'posts': post_count,
                    'trends': trend_count
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {e}"
            )
    
    def _check_api_keys(self) -> HealthCheckResult:
        """Check availability of required API keys"""
        required_keys = ['OPENAI_API_KEY']
        optional_keys = ['X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET', 'X_BEARER_TOKEN']
        
        missing_required = []
        missing_optional = []
        
        for key in required_keys:
            if not getattr(self.config, key, None):
                missing_required.append(key)
        
        for key in optional_keys:
            if not getattr(self.config, key, None):
                missing_optional.append(key)
        
        if missing_required:
            return HealthCheckResult(
                name="api_keys",
                status=HealthStatus.CRITICAL,
                message=f"Missing required API keys: {', '.join(missing_required)}",
                details={
                    'missing_required': missing_required,
                    'missing_optional': missing_optional
                }
            )
        elif missing_optional:
            return HealthCheckResult(
                name="api_keys",
                status=HealthStatus.WARNING,
                message=f"Missing optional API keys: {', '.join(missing_optional)}",
                details={
                    'missing_optional': missing_optional
                }
            )
        else:
            return HealthCheckResult(
                name="api_keys",
                status=HealthStatus.HEALTHY,
                message="All API keys configured"
            )
    
    def _check_disk_space(self) -> HealthCheckResult:
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            
            # Convert to GB
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            usage_percent = (used / total) * 100
            
            if usage_percent > 95:
                status = HealthStatus.CRITICAL
                message = f"Disk usage critical: {usage_percent:.1f}% used"
            elif usage_percent > 85:
                status = HealthStatus.WARNING
                message = f"Disk usage high: {usage_percent:.1f}% used"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {usage_percent:.1f}% used"
            
            return HealthCheckResult(
                name="disk_space",
                status=status,
                message=message,
                details={
                    'total_gb': round(total_gb, 2),
                    'used_gb': round(used_gb, 2),
                    'free_gb': round(free_gb, 2),
                    'usage_percent': round(usage_percent, 1)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"Could not check disk space: {e}"
            )
    
    def _check_memory_usage(self) -> HealthCheckResult:
        """Check memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            usage_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            if usage_percent > 95:
                status = HealthStatus.CRITICAL
                message = f"Memory usage critical: {usage_percent:.1f}% used"
            elif usage_percent > 85:
                status = HealthStatus.WARNING
                message = f"Memory usage high: {usage_percent:.1f}% used"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {usage_percent:.1f}% used"
            
            return HealthCheckResult(
                name="memory_usage",
                status=status,
                message=message,
                details={
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(available_gb, 2),
                    'usage_percent': round(usage_percent, 1)
                }
            )
            
        except ImportError:
            return HealthCheckResult(
                name="memory_usage",
                status=HealthStatus.UNKNOWN,
                message="psutil not available for memory monitoring"
            )
        except Exception as e:
            return HealthCheckResult(
                name="memory_usage",
                status=HealthStatus.UNKNOWN,
                message=f"Could not check memory usage: {e}"
            )
    
    def _check_recent_data(self) -> HealthCheckResult:
        """Check if recent data is being processed"""
        try:
            # Check for recent posts (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            recent_posts = db.session.query(Post).filter(
                Post.created_at >= cutoff_time
            ).count()
            
            # Check for recent trends (last 7 days)
            trend_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_trends = db.session.query(Trend).filter(
                Trend.created_at >= trend_cutoff
            ).count()
            
            if recent_posts == 0 and recent_trends == 0:
                status = HealthStatus.WARNING
                message = "No recent data processing detected"
            elif recent_posts == 0:
                status = HealthStatus.WARNING
                message = "No recent posts processed in last 24 hours"
            else:
                status = HealthStatus.HEALTHY
                message = f"Recent data processing active"
            
            return HealthCheckResult(
                name="recent_data",
                status=status,
                message=message,
                details={
                    'recent_posts_24h': recent_posts,
                    'recent_trends_7d': recent_trends
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="recent_data",
                status=HealthStatus.UNKNOWN,
                message=f"Could not check recent data: {e}"
            )
    
    def _check_cache_system(self) -> HealthCheckResult:
        """Check cache system functionality"""
        try:
            from utils.caching import cache_manager
            
            # Test cache operations
            test_key = f"health_check_{int(time.time())}"
            test_value = {"health_check": True, "timestamp": time.time()}
            
            # Test set
            set_result = cache_manager.set(test_key, test_value, ttl=60)
            if not set_result:
                return HealthCheckResult(
                    name="cache_system",
                    status=HealthStatus.WARNING,
                    message="Cache set operation failed"
                )
            
            # Test get
            retrieved = cache_manager.get(test_key)
            if retrieved != test_value:
                return HealthCheckResult(
                    name="cache_system",
                    status=HealthStatus.WARNING,
                    message="Cache get operation failed"
                )
            
            # Get cache stats
            stats = cache_manager.get_stats()
            
            # Clean up test key
            cache_manager.delete(test_key)
            
            return HealthCheckResult(
                name="cache_system",
                status=HealthStatus.HEALTHY,
                message=f"Cache system operational ({stats['cache_type']})",
                details=stats
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="cache_system",
                status=HealthStatus.WARNING,
                message=f"Cache system check failed: {e}"
            )
    
    def _check_background_tasks(self) -> HealthCheckResult:
        """Check background task system"""
        try:
            from utils.monitoring import task_monitor
            
            running_tasks = task_monitor.get_running_tasks()
            
            # Check for stale tasks (running > 6 hours)
            stale_count = task_monitor.cleanup_stale_tasks(max_age_hours=6)
            
            if len(running_tasks) > 10:
                status = HealthStatus.WARNING
                message = f"High number of running tasks: {len(running_tasks)}"
            elif stale_count > 0:
                status = HealthStatus.WARNING
                message = f"Cleaned up {stale_count} stale tasks"
            else:
                status = HealthStatus.HEALTHY
                message = "Background task system operational"
            
            return HealthCheckResult(
                name="background_tasks",
                status=status,
                message=message,
                details={
                    'running_tasks': len(running_tasks),
                    'cleaned_stale': stale_count
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="background_tasks",
                status=HealthStatus.WARNING,
                message=f"Background task check failed: {e}"
            )
    
    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """Determine overall system health status"""
        statuses = [result.status for result in results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif HealthStatus.UNKNOWN in statuses:
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

# Global health checker instance
health_checker = HealthChecker()