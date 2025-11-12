# web_api_bp/routes/api_routes.py

from flask import Blueprint, jsonify
from .. import services

# Blueprintを定義。URLプレフィックスは '/api' に設定
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/dashboard-data', methods=['GET'])
def dashboard_data():
    """
    JSの updateDashboard 関数が呼び出すエンドポイント
    servicesモジュールからデータを取得し、JSON形式で返す
    """
    try:
        data = services.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        # エラー処理。実際にはloggingモジュールで詳細を記録すべき
        return jsonify({"success": False, "error": str(e)}), 500


