from app import create_app
from flask import jsonify
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the main application
app = create_app()

# Add fast health endpoints for deployment that respond immediately
@app.route('/deployment-health')
def deployment_health():
    """Fastest possible health endpoint for deployment health checks"""
    return jsonify({
        'status': 'healthy',
        'service': 'ai-trends-analyzer',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/ping')
def ping():
    """Simple ping endpoint for load balancers"""
    return jsonify({'status': 'ok'}), 200

# Add root health endpoint for deployment platforms that check "/"
@app.route('/health-check')
def health_check():
    """Alternative health endpoint for deployment platforms"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
