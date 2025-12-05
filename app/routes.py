from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import time
from app.scheduler import refresh_now, update_interval, get_next_run_time, get_interval
from app.services.data_processor import get_current_model_info, switch_model

main = Blueprint('main', __name__)

DATA_FILE = os.path.join("data", "final_data.csv")

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/feed')
def live_feed():
    return render_template('feed.html')

@main.route('/clusters')
def clusters():
    return render_template('clusters.html')

@main.route('/data')
def raw_data():
    return render_template('data.html')

@main.route('/settings')
def settings():
    return render_template('settings.html')

@main.route('/api/data')
def get_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # Replace NaN with None (null in JSON)
            df = df.where(pd.notnull(df), None)
            return jsonify(df.to_dict(orient='records'))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify([]), 200

@main.route('/api/stats')
def get_stats():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            stats = {
                "total_articles": len(df),
                "high_risk": len(df[df['impact_level'] == 'High Risk']),
                "opportunity": len(df[df['impact_level'] == 'Opportunity']),
                "major_events": len(df[df['event_flag'] == 'Major Event']),
                "last_updated": time.ctime(os.path.getmtime(DATA_FILE))
            }
            return jsonify(stats)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"total_articles": 0, "high_risk": 0, "opportunity": 0, "major_events": 0, "last_updated": "Never"})

@main.route('/api/refresh', methods=['POST'])
def refresh_data():
    if refresh_now():
        return jsonify({"status": "success", "message": "Refresh triggered"}), 200
    else:
        return jsonify({"status": "error", "message": "Scheduler not running"}), 500

@main.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if request.method == 'POST':
        data = request.get_json()
        interval = data.get('interval')
        if interval and isinstance(interval, int) and interval >= 5:
            if update_interval(interval):
                return jsonify({"status": "success", "next_run": get_next_run_time()}), 200
            else:
                return jsonify({"status": "error", "message": "Failed to update scheduler"}), 500
        return jsonify({"status": "error", "message": "Invalid interval"}), 400
    else:
        return jsonify({
            "interval": get_interval(),
            "next_run": get_next_run_time()
        })

@main.route('/api/model', methods=['GET', 'POST'])
def api_model():
    if request.method == 'POST':
        data = request.get_json()
        model_name = data.get('model_name')
        if model_name:
            success, msg = switch_model(model_name)
            if success:
                return jsonify({"status": "success", "message": msg}), 200
            else:
                return jsonify({"status": "error", "message": msg}), 400
        return jsonify({"status": "error", "message": "Model name required"}), 400
    else:
        return jsonify(get_current_model_info())
