# web_app/routes/ui_routes.py

from flask import Blueprint, render_template, request

# Blueprintを定義。UIルートは通常、URLプレフィックスなし
ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/')
def dashboard():
    """ダッシュボード画面"""
    return render_template('dashboard.html')

@ui_bp.route('/sensors')
def sensors():
    """センサーグラフ画面"""
    return render_template('sensors.html')

@ui_bp.route('/gallery')
def gallery():
    """画像ギャラリー画面"""
    return render_template('gallery.html')

@ui_bp.route('/ai-reports')
def ai_reports():
    """AI相談チャット画面"""
    return render_template('ai_chat.html')

@ui_bp.route('/schedules')
def schedules():
    """スケジュール管理画面"""
    return render_template('schedules.html')

@ui_bp.route('/settings')
def settings():
    """システム設定画面"""
    return render_template('settings.html')

@ui_bp.route('/logs')
def logs():
    """システムログ画面"""
    return render_template('logs.html')


@ui_bp.route('/plant_images/<path:filename>')
def serve_plant_images(filename):
    """plant_images ディレクトリの画像を配信"""
    # 親ディレクトリのplant_imagesを参照
    parent_dir = Path(__file__).parent.parent
    return send_from_directory(parent_dir / 'plant_images', filename)

