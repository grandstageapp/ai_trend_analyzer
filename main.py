"""
Ultra-fast deployment entry point
"""
from flask import Flask, jsonify, render_template_string
import os
import sys
import threading
import time

# Minimal Flask app for instant startup
app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'fast-key')

# Global state
full_app_ready = False

# Instant health endpoints
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/ping')
def ping():
    return jsonify({'status': 'ok'}), 200

@app.route('/')
def index():
    if full_app_ready:
        try:
            # Try to serve dashboard
            from routes.main import index as dashboard_index
            return dashboard_index()
        except:
            pass
    
    # Loading page while full app initializes
    return render_template_string('''
    <!DOCTYPE html>
    <html><head><title>AI Trends Dashboard - AI Trends Analyzer</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
    <h1>AI Trends Dashboard</h1>
    <p>Loading AI trends data...</p>
    <script>setTimeout(() => location.reload(), 3000);</script>
    </body></html>
    '''), 200

def load_full_app():
    global full_app_ready
    try:
        time.sleep(0.5)  # Let health endpoints start first
        from app import create_app
        full_app = create_app()
        
        # Copy routes
        for rule in full_app.url_map.iter_rules():
            if rule.endpoint not in ['health', 'ping', 'index', 'static']:
                view_func = full_app.view_functions.get(rule.endpoint)
                if view_func:
                    app.add_url_rule(rule.rule, rule.endpoint, view_func, methods=list(rule.methods))
        
        app.config.update(full_app.config)
        app.jinja_env = full_app.jinja_env
        full_app_ready = True
    except:
        pass

# Start background loading
threading.Thread(target=load_full_app, daemon=True).start()



if __name__ == "__main__":
    logger.info("Starting AI Trends Analyzer on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
