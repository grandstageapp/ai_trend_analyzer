"""
Optimized deployment entry point
"""
from app import create_app
from flask import jsonify
import logging

# Minimal logging for deployment
logging.basicConfig(level=logging.CRITICAL)

# Create application using factory pattern
app = create_app()

# Add fast health endpoints for deployment health checks
@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

@app.route('/ping')
def ping():
    return {'status': 'ok'}, 200



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
