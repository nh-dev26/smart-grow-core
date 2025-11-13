# web_api_bp/routes/api_routes.py
from flask import Blueprint, jsonify, request
from datetime import datetime
from .. import services

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
        
        ai_response = services.process_ai_chat(user_message, image_filename, sensor_data)
        
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
