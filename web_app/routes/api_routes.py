# smart-grow-core/web_app/routes/api_routes.py

from flask import Blueprint, jsonify, request
# requests は不要になります
from database.db_manager import get_latest_tank_status, select_schedules

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')

@api_bp.route('/status', methods=['GET'])
def get_current_status():
    """
    データベースから最新の状態を取得する。
    これにより、コア機能の稼働状態に依存しなくなる。
    """
    try:
        # 例として、最新のタンク状態とスケジュールを取得
        # 複数の層がある場合は、リクエストから layer_id を受け取る
        layer_id = request.args.get('layer_id', 1, type=int)
        
        latest_status = get_latest_tank_status(layer_id)
        schedules = select_schedules()
        
        return jsonify({
            "latest_status": latest_status,
            "schedules": schedules
        })
    except Exception as e:
        return jsonify({"error": "Failed to fetch status from database", "details": str(e)}), 500

# 手動制御などのAPIも、直接ハードウェアを叩くのではなく、
# DBに「手動実行フラグ」を立て、コア機能がそれを検知して実行する、
# という形にすると、より疎結合になります。