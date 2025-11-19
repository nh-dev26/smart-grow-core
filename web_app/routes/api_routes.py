from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from web_app import services
from config import DEFAULT_SYSTEM_CONFIG

# Blueprintを定義。URLプレフィックスは '/api' に設定
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/dashboard-data')
def api_dashboard_data():
    """ダッシュボード用のデータをJSON形式で返す"""
    try:
        image_layer_id = request.args.get('layer_id', 1, type=int)
        data = services.select_dashboard_data(image_layer_id)
        return jsonify({'success': True, **data})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
@api_bp.route('/sensor-history')
def api_sensor_history():
    """センサー履歴データを取得（グラフ用）"""
    try:
        hours = request.args.get('hours', 24, type=int)
        result = services.select_sensor_history(hours)
        return jsonify({'success': True, **result})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
@api_bp.route('/images')
def api_images():
    """画像一覧を取得（ファイルシステムから直接）"""
    try:
        layer_id = request.args.get('layer_id', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        images = services.select_images(layer_id, limit)
        return jsonify({
            'success': True,
            'images': images
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
@api_bp.route('/ai-reports-list')
def api_ai_reports_list():
    """AI解析レポート一覧を取得"""
    try:
        layer_id = request.args.get('layer_id', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        reports = services.select_ai_reports(layer_id, limit)
        return jsonify({
            'success': True,
            'reports': reports
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/logs-list')
def api_logs_list():
    """システムログ一覧を取得"""
    try:
        log_level = request.args.get('log_level', None)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        logs = services.select_logs(log_level, limit, offset)
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
@api_bp.route('/system-config')
def api_system_config():
    """システム設定を取得"""
    try:
        config = services.select_system_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/schedules')
def api_schedules_list():
    """スケジュール一覧を取得"""
    try:
        schedules = services.select_schedules()
        return jsonify({
            'success': True,
            'schedules': schedules
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
@api_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
def api_schedule_update(schedule_id):
    """スケジュールを更新"""
    try:
        data = request.get_json()
        exec_time = data.get('exec_time')
        is_enabled = data.get('is_enabled')
        
        services.update_schedule(schedule_id, exec_time, is_enabled)
        return jsonify({
            'success': True,
            'message': 'Schedule updated successfully'
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/schedules/<int:schedule_id>/toggle', methods=['PATCH'])
def api_schedule_toggle(schedule_id):
    """スケジュールの有効/無効を切り替え"""
    try:
        new_state = services.toggle_schedule(schedule_id)
        if new_state is None:
            return jsonify({'success': False, 'error': 'Schedule not found'}), 404

        return jsonify({
            'success': True,
            'is_enabled': bool(new_state)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/ai-chat', methods=['POST'])
def api_ai_chat():
    """AI チャット API - Gemini API を使用"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        image_filename = data.get('image_filename')
        sensor_data = data.get('sensor_data', {})
        
        if not user_message:
            return jsonify({'error': 'メッセージが空です'}), 400
        
        ai_response = services.process_ai_chat(user_message, image_filename, sensor_data, current_app.root_path)
        
        return jsonify({
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except ConnectionError as e:
        return jsonify({'error': str(e)}), 503
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"API エラー: {e}")
        return jsonify({'error': str(e)}), 500

THRESHOLD_KEYS = [
    "water_duration_sec", 
    "temp_high_threshold", 
    "temp_low_threshold", 
    "supply_low_threshold", 
    "drain_high_threshold",
    "pump_gpio_sig",    
    "i2c_bus_num"       
]

INTEGRATION_KEYS = [
    "llm_model_name"
]
# 個別リセット可能な全てのキーを統合
ALL_CONFIG_KEYS = THRESHOLD_KEYS + INTEGRATION_KEYS 

# ------------------------------------------
# 1. 設定保存 API
# ------------------------------------------

@api_bp.route('/settings/thresholds', methods=['POST'])
def update_thresholds():
    """制御・閾値設定 (ハードウェア設定を含む) をDBに保存する"""
    try:
        data = request.get_json()
        
        # 受け取ったデータから、THRESHOLD_KEYSに該当する項目のみを抽出
        update_data = {key: data[key] for key in THRESHOLD_KEYS if key in data}
        
        # サービス層にDB更新を依頼
        if services.update_system_config(update_data):
            return jsonify({
                "success": True, 
                "message": "制御・閾値設定を正常に保存しました。"
            })
        else:
            return jsonify({"success": False, "error": "DB更新処理に失敗しました。"}), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"制御・閾値設定の保存中にエラーが発生しました: {str(e)}"
        }), 500

@api_bp.route('/settings/integrations', methods=['POST'])
def update_integrations():
    """連携設定をDBに保存する"""
    try:
        data = request.get_json()
        
        # 受け取ったデータから、INTEGRATION_KEYSに該当する項目のみを抽出
        update_data = {key: data[key] for key in INTEGRATION_KEYS if key in data}
        
        if services.update_system_config(update_data):
            return jsonify({
                "success": True, 
                "message": "連携設定を正常に保存しました。"
            })
        else:
            return jsonify({"success": False, "error": "DB更新処理に失敗しました。"}), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"連携設定の保存中にエラーが発生しました: {str(e)}"
        }), 500

# ------------------------------------------
# 2. 全体リセット API
# ------------------------------------------

@api_bp.route('/settings/thresholds/reset', methods=['POST'])
def reset_all_thresholds():
    """制御・閾値設定（全て）をデフォルト値にリセットする"""
    try:
        # THRESHOLD_KEYS に該当する全てのキーとそのデフォルト値を取得
        reset_data = {key: DEFAULT_SYSTEM_CONFIG[key] for key in THRESHOLD_KEYS}
        
        # サービス層にDB更新を依頼
        if services.update_system_config(reset_data):
            return jsonify({
                "success": True, 
                "message": "制御・閾値設定の全てがデフォルトにリセットされました。"
            })
        else:
            return jsonify({"success": False, "error": "DBリセット処理に失敗しました。"}), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"制御・閾値の全体リセット中にエラーが発生しました: {str(e)}"
        }), 500

@api_bp.route('/settings/integrations/reset', methods=['POST'])
def reset_all_integrations():
    """連携設定（全て）をデフォルト値にリセットする"""
    try:
        # INTEGRATION_KEYS に該当する全てのキーとそのデフォルト値を取得
        reset_data = {key: DEFAULT_SYSTEM_CONFIG[key] for key in INTEGRATION_KEYS}
        
        # サービス層にDB更新を依頼
        if services.update_system_config(reset_data):
            return jsonify({
                "success": True, 
                "message": "連携設定の全てがデフォルトにリセットされました。"
            })
        else:
            return jsonify({"success": False, "error": "DBリセット処理に失敗しました。"}), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"連携設定の全体リセット中にエラーが発生しました: {str(e)}"
        }), 500

# ------------------------------------------
# 3. 個別リセット API
# ------------------------------------------

# 既存の @api_bp.route('/settings/reset', methods=['POST']) を以下の内容に置き換えます

@api_bp.route('/settings/reset', methods=['POST'])
def reset_single_setting():
    """
    指定された単一キーの設定をデフォルト値にリセットする。
    リクエストボディ: {"key": "water_duration_sec"}
    """
    try:
        data = request.get_json()
        target_key = data.get('key')
        
        if not target_key:
            return jsonify({"success": False, "error": "キー名 (key) が指定されていません。"}), 400
            
        # ALL_CONFIG_KEYS を使用して、制御・閾値と連携設定のどちらもリセット可能にする
        if target_key not in ALL_CONFIG_KEYS: 
            return jsonify({"success": False, "error": f"キー '{target_key}' は設定項目として無効です。"}), 403
            
        default_value = DEFAULT_SYSTEM_CONFIG.get(target_key)
        
        if default_value is None:
            return jsonify({"success": False, "error": f"キー '{target_key}' のデフォルト値が見つかりません。"}), 400
            
        # サービス関数を呼び出し、DBを更新
        # 注: サービス関数の名前を services.update_single_system_config_key に修正して呼び出しています
        if services.update_single_system_config_key(target_key, default_value):
            return jsonify({
                "success": True,
                "key": target_key,
                "default_value": default_value,
                "message": f"'{target_key}' がデフォルト値にリセットされました。"
            })
        else:
            return jsonify({"success": False, "error": "DB更新処理に失敗しました。"}), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"サーバーエラーが発生しました: {str(e)}"
        }), 500