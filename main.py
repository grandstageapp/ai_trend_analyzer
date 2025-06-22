"""
AI Trends Analyzer - Dual Mode Entry Point
"""
import os

# Check if we're in deployment mode (deployment env vars or production indicators)
if (os.environ.get('REPL_DEPLOYMENT') or 
    os.environ.get('RAILWAY_ENVIRONMENT') or 
    os.environ.get('RENDER') or
    os.environ.get('VERCEL') or
    'gunicorn' in os.environ.get('SERVER_SOFTWARE', '')):
    # Ultra-fast deployment mode
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    app.secret_key = os.environ.get('SESSION_SECRET', 'deploy-key')
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    @app.route('/ping')
    def ping():
        return {'status': 'ok'}, 200
    
    @app.route('/')
    def root():
        return {'status': 'ok', 'service': 'ai-trends-analyzer'}, 200

else:
    # Full development mode
    from app import create_app
    from flask import jsonify
    import logging
    
    logging.basicConfig(level=logging.ERROR)
    
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
