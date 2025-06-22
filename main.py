"""
AI Trends Analyzer - Production Ready
"""
from app import create_app
from flask import jsonify
import logging
import os

# Configure minimal logging 
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

# Create the application
app = create_app()

# Add ultra-fast health endpoints that bypass all middleware
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200, {'Content-Type': 'application/json'}

@app.route('/ping', methods=['GET']) 
def ping():
    return jsonify({'status': 'ok'}), 200, {'Content-Type': 'application/json'}



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
