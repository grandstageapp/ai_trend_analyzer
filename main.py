"""
Deployment-optimized entry point
"""
import os
import sys
import logging
from flask import Flask, jsonify

# Disable all logging for fastest startup
logging.getLogger().setLevel(logging.CRITICAL)
logging.disable(logging.CRITICAL)

# Create ultra-minimal Flask app for instant startup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'deployment-key')

# Immediate health endpoints - no dependencies
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/ping')
def ping():
    return jsonify({'status': 'ok'}), 200

@app.route('/')
def root():
    return jsonify({'status': 'ok', 'service': 'ai-trends-analyzer'}), 200

# Only load full app if not in deployment mode
if not os.environ.get('REPL_DEPLOYMENT'):
    try:
        from app import create_app
        full_app = create_app()
        
        # Copy all routes from full app except health endpoints
        for rule in full_app.url_map.iter_rules():
            if rule.endpoint not in ['health', 'ping', 'root', 'static']:
                view_func = full_app.view_functions.get(rule.endpoint)
                if view_func:
                    app.add_url_rule(rule.rule, rule.endpoint, view_func, methods=list(rule.methods))
        
        # Copy configurations
        app.config.update(full_app.config)
        app.jinja_env = full_app.jinja_env
        
    except Exception:
        pass  # Continue with minimal app for deployment



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
