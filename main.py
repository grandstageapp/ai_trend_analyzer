from app import create_app
from flask import jsonify
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the main application
app = create_app()

# Add health check endpoints for deployment (NOT on root path to preserve homepage)
@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms"""
    return {'status': 'healthy', 'service': 'ai-trends-analyzer'}, 200

@app.route('/ping')
def ping():
    """Simple ping endpoint for load balancers"""
    return {'status': 'ok'}, 200



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
