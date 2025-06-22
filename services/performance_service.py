"""
Performance monitoring and optimization service
"""
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
from utils.caching import cache_manager
from utils.query_optimization import query_optimizer

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor and optimize application performance"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.slow_queries = []
        self.cache_performance = {}
        
    def track_execution_time(self, operation_name: str):
        """Decorator to track execution time of operations"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Log slow operations (>1 second)
                    if execution_time > 1.0:
                        logger.warning(f"Slow operation detected: {operation_name} took {execution_time:.2f}s")
                        self.slow_queries.append({
                            'operation': operation_name,
                            'execution_time': execution_time,
                            'timestamp': datetime.utcnow(),
                            'function': func.__name__
                        })
                    
                    # Store metrics
                    self.metrics[operation_name].append({
                        'execution_time': execution_time,
                        'timestamp': datetime.utcnow(),
                        'success': True
                    })
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    # Log failed operations
                    logger.error(f"Operation failed: {operation_name} after {execution_time:.2f}s - {e}")
                    self.metrics[operation_name].append({
                        'execution_time': execution_time,
                        'timestamp': datetime.utcnow(),
                        'success': False,
                        'error': str(e)
                    })
                    
                    raise
                    
            return wrapper
        return decorator
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        summary = {
            'time_period_hours': hours,
            'operations': {},
            'slow_queries': [],
            'cache_performance': cache_manager.get_stats(),
            'database_stats': query_optimizer.get_database_performance_stats()
        }
        
        # Analyze operation metrics
        for operation, metrics_list in self.metrics.items():
            recent_metrics = [
                m for m in metrics_list 
                if m['timestamp'] > cutoff_time
            ]
            
            if recent_metrics:
                execution_times = [m['execution_time'] for m in recent_metrics]
                successful_ops = [m for m in recent_metrics if m['success']]
                
                summary['operations'][operation] = {
                    'total_calls': len(recent_metrics),
                    'successful_calls': len(successful_ops),
                    'failure_rate': (len(recent_metrics) - len(successful_ops)) / len(recent_metrics) * 100,
                    'avg_execution_time': sum(execution_times) / len(execution_times),
                    'max_execution_time': max(execution_times),
                    'min_execution_time': min(execution_times)
                }
        
        # Get recent slow queries
        summary['slow_queries'] = [
            sq for sq in self.slow_queries 
            if sq['timestamp'] > cutoff_time
        ]
        
        return summary
    
    def optimize_recommendations(self) -> List[Dict[str, str]]:
        """Generate optimization recommendations based on performance data"""
        recommendations = []
        
        # Analyze cache hit rate
        cache_stats = cache_manager.get_stats()
        if cache_stats['hit_rate_percent'] < 70:
            recommendations.append({
                'type': 'caching',
                'priority': 'high',
                'description': f"Cache hit rate is {cache_stats['hit_rate_percent']:.1f}% (target: >70%)",
                'recommendation': 'Consider increasing cache TTL for frequently accessed data or review cache key strategies'
            })
        
        # Analyze slow operations
        recent_summary = self.get_performance_summary(hours=1)
        for operation, stats in recent_summary['operations'].items():
            if stats['avg_execution_time'] > 2.0:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'description': f"Operation '{operation}' averages {stats['avg_execution_time']:.2f}s",
                    'recommendation': 'Consider query optimization, indexing, or caching for this operation'
                })
            
            if stats['failure_rate'] > 10:
                recommendations.append({
                    'type': 'reliability',
                    'priority': 'high',
                    'description': f"Operation '{operation}' has {stats['failure_rate']:.1f}% failure rate",
                    'recommendation': 'Investigate error patterns and improve error handling'
                })
        
        # Analyze database performance
        db_stats = recent_summary.get('database_stats', {})
        if 'table_stats' in db_stats:
            for table in db_stats['table_stats']:
                # Check for tables with high sequential scans
                if table['seq_scan'] > table.get('idx_scan', 0) * 2:
                    recommendations.append({
                        'type': 'database',
                        'priority': 'medium',
                        'description': f"Table '{table['tablename']}' has high sequential scan ratio",
                        'recommendation': 'Consider adding indexes for frequently queried columns'
                    })
        
        return recommendations
    
    def clear_old_metrics(self, days: int = 7):
        """Clear metrics older than N days"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        cleared_count = 0
        
        for operation in list(self.metrics.keys()):
            original_count = len(self.metrics[operation])
            self.metrics[operation] = [
                m for m in self.metrics[operation] 
                if m['timestamp'] > cutoff_time
            ]
            cleared_count += original_count - len(self.metrics[operation])
        
        # Clear old slow queries
        self.slow_queries = [
            sq for sq in self.slow_queries 
            if sq['timestamp'] > cutoff_time
        ]
        
        logger.info(f"Cleared {cleared_count} old performance metrics")
        return cleared_count

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Decorators for easy use
def track_performance(operation_name: str):
    """Decorator to track performance of operations"""
    return performance_monitor.track_execution_time(operation_name)