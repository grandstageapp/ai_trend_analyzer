"""
Main application entry point optimized for deployment
"""
import logging
import os
import sys

# Configure minimal logging for fastest startup
logging.basicConfig(level=logging.CRITICAL)

# Always use the full application with optimized startup
from app import create_app
from flask import jsonify

app = create_app()

@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200

@app.route('/ping')
def ping():
    return {'status': 'ok'}, 200



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
