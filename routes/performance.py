"""
Performance monitoring routes for Phase 3 optimization
"""
from flask import Blueprint, jsonify, request
from services.performance_service import performance_monitor
from utils.caching import cache_manager
from utils.query_optimization import query_optimizer

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')

@performance_bp.route('/stats')
def get_performance_stats():
    """Get current performance statistics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        summary = performance_monitor.get_performance_summary(hours=hours)
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/cache/stats')
def get_cache_stats():
    """Get cache performance statistics"""
    try:
        stats = cache_manager.get_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear cache with optional pattern"""
    try:
        pattern = request.json.get('pattern', '*') if request.json else '*'
        cleared = cache_manager.clear_pattern(pattern)
        
        return jsonify({
            'success': True,
            'cleared_keys': cleared
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/database/stats')
def get_database_stats():
    """Get database performance statistics"""
    try:
        stats = query_optimizer.get_database_performance_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@performance_bp.route('/recommendations')
def get_optimization_recommendations():
    """Get optimization recommendations"""
    try:
        recommendations = performance_monitor.optimize_recommendations()
        return jsonify({
            'success': True,
            'data': recommendations
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500