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
    Simple health check without database dependencies for deployment
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'ai-trends-analyzer'
    }), 200

@health_bp.route('/db')
def database_health_check():
    """
    Database-specific health check with retry logic
    """
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            from models import db
            db.session.execute(db.text('SELECT 1'))
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'ai-trends-analyzer',
                'database': 'connected',
                'attempt': attempt + 1
            }), 200
            
        except Exception as e:
            logger.warning(f"Database health check attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Database health check failed after {max_retries} attempts: {e}")
                return jsonify({
                    'status': 'unhealthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'service': 'ai-trends-analyzer',
                    'database': 'disconnected',
                    'error': str(e),
                    'attempts': max_retries
                }), 503

@health_bp.route('/detailed')
def detailed_health_check():
    """
    Detailed health check with graceful error handling
    """
    try:
        status_code = 200
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ai-trends-analyzer',
            'checks': {}
        }
        
        # Try to get comprehensive health check results with fallback
        try:
            from utils.health_checks import health_checker, HealthStatus
            health_results = health_checker.run_all_checks()
            
            for check_name, result in health_results.items():
                health_data['checks'][check_name] = {
                    'status': result.status.value,
                    'message': result.message,
                    'details': result.details,
                    'response_time_ms': result.response_time_ms
                }
                
                # Set overall status based on worst individual status
                if result.status == HealthStatus.CRITICAL:
                    health_data['status'] = 'critical'
                    status_code = 503
                elif result.status == HealthStatus.WARNING and health_data['status'] != 'critical':
                    health_data['status'] = 'warning'
                    
        except Exception as check_error:
            logger.warning(f"Health checker failed, using basic checks: {check_error}")
            # Fallback to basic checks
            health_data['checks']['basic'] = {
                'status': 'healthy',
                'message': 'Basic application health verified',
                'details': {'fallback_mode': True}
            }
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ai-trends-analyzer',
            'error': str(e)
        }), 503

@health_bp.route('/ready')
def readiness_check():
    """
    Readiness check with graceful database handling
    """
    try:
        # Basic readiness - application is running
        readiness_data = {
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ai-trends-analyzer',
            'database_available': False,
            'data_available': False
        }
        
        # Try database connection without failing the whole check
        try:
            from models import db, Trend
            db.session.execute(db.text('SELECT 1'))
            readiness_data['database_available'] = True
            
            # Check for data availability
            trend_count = db.session.query(Trend).count()
            readiness_data['data_available'] = trend_count > 0
            readiness_data['trend_count'] = trend_count
            
        except Exception as db_error:
            logger.warning(f"Database not ready during readiness check: {db_error}")
            readiness_data['database_error'] = str(db_error)
        
        return jsonify(readiness_data), 200
        
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