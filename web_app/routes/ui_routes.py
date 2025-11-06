# smart-grow-core/web_app/routes/ui_routes.py

from flask import Blueprint, render_template

ui_bp = Blueprint('ui_bp', __name__)

@ui_bp.route('/')
@ui_bp.route('/dashboard')
def dashboard():
    """ダッシュボード画面。APIからデータを取得し、Jinja2でレンダリング"""
    # ここで services.py を通してデータを取得
    status_data = {"temp": 25.0, "pump_status": "ON"} # 例: services.get_status()
    return render_template('dashboard.html', data=status_data)

@ui_bp.route('/logs')
def logs():
    """ログ履歴画面。DBからログデータを取得"""
    # logs = services.get_historical_logs() # 例
    return render_template('logs.html', logs=[])