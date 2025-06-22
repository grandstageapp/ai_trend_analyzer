from app import create_app
from flask import jsonify
import logging
import os

# Configure logging for faster startup
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Create the main application using existing factory
app = create_app()

# Add deployment health endpoints that respond immediately
@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms"""
    return {'status': 'healthy', 'service': 'ai-trends-analyzer'}, 200

@app.route('/ping')
def ping():
    """Ping endpoint for load balancers"""
    return {'status': 'ok'}, 200



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
