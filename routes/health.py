"""
Health monitoring and alerting routes
"""
from flask import Blueprint, jsonify, request
from utils.health_checks import health_checker, HealthStatus
from utils.alerting import alert_manager, AlertSeverity
from services.performance_service import performance_monitor
from utils.caching import cache_manager

health_bp = Blueprint('health', __name__, url_prefix='/api/health')

@health_bp.route('/')
def health_status():
    """Get overall system health status"""
    try:
        results = health_checker.run_all_checks()
        overall_status = health_checker.get_overall_status(results)
        
        # Check results for alerts
        alert_manager.check_health_results(results)
        
        return jsonify({
            'status': overall_status.value,
            'timestamp': results[list(results.keys())[0]].timestamp.isoformat(),
            'checks': {
                name: {
                    'status': result.status.value,
                    'message': result.message,
                    'response_time_ms': result.response_time_ms,
                    'details': result.details
                }
                for name, result in results.items()
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {e}'
        }), 500

@health_bp.route('/check/<check_name>')
def individual_health_check(check_name):
    """Run a specific health check"""
    try:
        if check_name not in health_checker.checks:
            return jsonify({
                'error': f'Unknown health check: {check_name}',
                'available_checks': list(health_checker.checks.keys())
            }), 404
        
        check_func = health_checker.checks[check_name]
        result = check_func()
        
        return jsonify({
            'check_name': check_name,
            'status': result.status.value,
            'message': result.message,
            'response_time_ms': result.response_time_ms,
            'details': result.details,
            'timestamp': result.timestamp.isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Health check failed: {e}'
        }), 500

@health_bp.route('/alerts')
def get_alerts():
    """Get active alerts"""
    try:
        severity_filter = request.args.get('severity')
        severity = None
        
        if severity_filter:
            try:
                severity = AlertSeverity(severity_filter.lower())
            except ValueError:
                return jsonify({
                    'error': f'Invalid severity: {severity_filter}',
                    'valid_severities': [s.value for s in AlertSeverity]
                }), 400
        
        alerts = alert_manager.get_active_alerts(severity)
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get alerts: {e}'
        }), 500

@health_bp.route('/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve a specific alert"""
    try:
        success = alert_manager.resolve_alert(alert_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Alert {alert_id} resolved'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Alert {alert_id} not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'error': f'Failed to resolve alert: {e}'
        }), 500

@health_bp.route('/alerts/summary')
def get_alert_summary():
    """Get alert summary statistics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        summary = alert_manager.get_alert_summary(hours)
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get alert summary: {e}'
        }), 500

@health_bp.route('/metrics')
def get_health_metrics():
    """Get comprehensive health and performance metrics"""
    try:
        # Get health check results
        health_results = health_checker.run_all_checks()
        
        # Get performance metrics
        perf_summary = performance_monitor.get_performance_summary(hours=1)
        
        # Get cache statistics
        cache_stats = cache_manager.get_stats()
        
        # Get alert summary
        alert_summary = alert_manager.get_alert_summary(hours=24)
        
        return jsonify({
            'health': {
                name: {
                    'status': result.status.value,
                    'message': result.message,
                    'response_time_ms': result.response_time_ms
                }
                for name, result in health_results.items()
            },
            'performance': perf_summary,
            'cache': cache_stats,
            'alerts': alert_summary,
            'timestamp': health_results[list(health_results.keys())[0]].timestamp.isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get metrics: {e}'
        }), 500

@health_bp.route('/diagnostics')
def run_diagnostics():
    """Run comprehensive system diagnostics"""
    try:
        diagnostics = {}
        
        # Health checks
        health_results = health_checker.run_all_checks()
        diagnostics['health_checks'] = {
            name: result.status.value for name, result in health_results.items()
        }
        
        # Performance recommendations
        recommendations = performance_monitor.optimize_recommendations()
        diagnostics['recommendations'] = recommendations
        
        # System resources
        import psutil
        try:
            diagnostics['system'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except:
            diagnostics['system'] = {'error': 'System metrics unavailable'}
        
        # Recent errors (if any)
        recent_alerts = alert_manager.get_active_alerts()
        critical_alerts = [a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]
        
        diagnostics['critical_issues'] = len(critical_alerts)
        diagnostics['total_active_alerts'] = len(recent_alerts)
        
        return jsonify(diagnostics)
        
    except Exception as e:
        return jsonify({
            'error': f'Diagnostics failed: {e}'
        }), 500