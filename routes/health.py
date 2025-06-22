"""
Health check routes for deployment monitoring and system status
"""
import logging
from flask import Blueprint, jsonify, request
from utils.health_checks import health_checker
from datetime import datetime

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.route('/')
def health_check():
    """
    Main health check endpoint for deployment monitoring
    Returns basic system status for load balancers and monitoring tools
    """
    try:
        # Quick database connectivity check
        from models import db
        db.session.execute(db.text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ai-trends-analyzer'
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ai-trends-analyzer',
            'error': str(e)
        }), 503

@health_bp.route('/detailed')
def detailed_health_check():
    """
    Detailed health check with comprehensive system status
    """
    try:
        # Run all health checks
        results = health_checker.run_all_checks()
        overall_status = health_checker.get_overall_status(results)
        
        # Convert results to JSON-serializable format
        response_data = {
            'overall_status': overall_status.value,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ai-trends-analyzer',
            'checks': {}
        }
        
        for check_name, result in results.items():
            response_data['checks'][check_name] = {
                'status': result.status.value,
                'message': result.message,
                'response_time_ms': result.response_time_ms,
                'details': result.details
            }
        
        # Return appropriate HTTP status code
        status_code = 200 if overall_status.value == 'healthy' else 503
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            'overall_status': 'critical',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ai-trends-analyzer',
            'error': str(e)
        }), 503

@health_bp.route('/ready')
def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration
    """
    try:
        # Check critical components for readiness
        from models import db, Trend
        
        # Verify database connection and basic data availability
        db.session.execute(db.text('SELECT 1'))
        trend_count = db.session.query(Trend).count()
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ai-trends-analyzer',
            'data_available': trend_count > 0
        }), 200
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ai-trends-analyzer',
            'error': str(e)
        }), 503

@health_bp.route('/live')
def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration
    Simple check to verify the application is running
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'ai-trends-analyzer'
    }), 200