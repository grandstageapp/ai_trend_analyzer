"""
AI Trends Analyzer - Main Entry Point
"""
from app import create_app
from flask import jsonify
import logging

# Minimal logging for deployment performance
logging.basicConfig(level=logging.ERROR)

# Create the full application
app = create_app()

# Add deployment health endpoints
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/ping')
def ping():
    return jsonify({'status': 'ok'}), 200



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
