from app import create_app
from flask import jsonify
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the full application but with health endpoints first
app = create_app()

# Override root route with health check for deployment
@app.route('/', methods=['GET'])
def root_health():
    """Root health check for deployment - responds immediately"""
    return jsonify({
        'status': 'healthy',
        'service': 'ai-trends-analyzer',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Simple health endpoint"""
    return jsonify({'status': 'ok'}), 200

@app.route('/ping', methods=['GET'])
def ping():
    """Ping endpoint for load balancers"""
    return jsonify({'status': 'ok'}), 200



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
