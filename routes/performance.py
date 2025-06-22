"""
Performance monitoring routes for system metrics and optimization
"""
import logging
from flask import Blueprint, jsonify, request
from services.performance_service import PerformanceMonitor
from datetime import datetime

logger = logging.getLogger(__name__)
performance_bp = Blueprint('performance', __name__, url_prefix='/performance')

# Initialize performance monitor
performance_monitor = PerformanceMonitor()

@performance_bp.route('/metrics')
def performance_metrics():
    """
    Get performance metrics for the application
    """
    try:
        hours = request.args.get('hours', 24, type=int)
        
        # Get performance summary
        metrics = performance_monitor.get_performance_summary(hours=hours)
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics,
            'period_hours': hours
        }), 200
        
    except Exception as e:
        logger.error(f"Performance metrics failed: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@performance_bp.route('/recommendations')
def optimization_recommendations():
    """
    Get optimization recommendations based on performance data
    """
    try:
        recommendations = performance_monitor.optimize_recommendations()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        logger.error(f"Performance recommendations failed: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500