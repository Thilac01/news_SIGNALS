from flask import Flask
from app.scheduler import start_scheduler

def create_app():
    app = Flask(__name__)
    
    # Register Blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    # Start Scheduler
    # We only want to start the scheduler if we are not in debug mode reloader
    # or we handle it to not run twice. 
    # For simplicity in this setup, we'll just start it.
    # In production with gunicorn, this might need a different approach (e.g. separate worker).
    # But for "industrial format" single app usage, this is fine.
    import os
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_scheduler()

    return app
