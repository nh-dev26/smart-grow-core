# smart-grow-core/web_app/routes/api_routes.py

from flask import Blueprint, jsonify, request
import requests # main.py のローカルAPIと通信するため

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')
HW_CONTROL_URL = 'http://127.0.0.1:5001' # main.py の API アドレス

@api_bp.route('/status', methods=['GET'])
def get_current_status():
    """リアルタイムの状態（main.pyプロセスで管理）を取得"""
    try:
        # main.py のローカルAPIへ接続し、状態を取得
        response = requests.get(f"{HW_CONTROL_URL}/status", timeout=2)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException:
        return jsonify({"error": "HW core offline"}), 503

@api_bp.route('/control', methods=['POST'])
def post_control_command():
    """制御コマンドを main.py プロセスへ転送"""
    data = request.get_json()
    action = data.get('action') # 例: 'pump_on'

    try:
        # main.py のローカルAPIへ指令を転送
        response = requests.post(f"{HW_CONTROL_URL}/control/pump", json={'action': action})
        response.raise_for_status()
        return jsonify({"message": "Command sent successfully"}), 200
    except requests.exceptions.RequestException:
        return jsonify({"error": "Failed to send command to core"}), 503