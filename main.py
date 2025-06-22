"""
AI Trends Analyzer - Optimized Entry Point
"""
from app import create_app
from flask import jsonify
import logging

# Minimal logging
logging.basicConfig(level=logging.ERROR)

# Create the application
app = create_app()

# Health endpoints
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/ping')
def ping():
    return jsonify({'status': 'ok'}), 200



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
