# web_app/services.py

import os
import glob
import io
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image

from database.db_manager import (
    open_db,
    select_latest_sensor_data as db_select_latest_sensor_data,
    select_latest_image_info as db_select_latest_image_info,
    select_recent_alerts as db_select_recent_alerts,
    select_next_schedules as db_select_next_schedules,
    select_system_config
)
from core.ai_manager import gemini_model, create_system_prompt


def select_dashboard_data(image_layer_id=1):
    """ダッシュボード用のデータを取得する"""
    sensor_data = db_select_latest_sensor_data(layer_id=0)
    latest_image = db_select_latest_image_info(image_layer_id)
    alerts = db_select_recent_alerts(5)
    next_schedules = db_select_next_schedules(3)
    
    return {
        'sensor_data': sensor_data,
        'latest_image': latest_image,
        'alerts': alerts,
        'next_schedules': next_schedules,
        'timestamp': datetime.now().isoformat()
    }

def select_sensor_history(hours=24):
    """センサー履歴データを取得する"""
    layer_id = 0
    start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

    if hours <= 24:
        interval_minutes = None
    elif hours <= 168:
        interval_minutes = 120
    else:
        interval_minutes = 360

    with open_db() as conn:
        cursor = conn.cursor()
        if interval_minutes is None:
            cursor.execute("""
                SELECT timestamp, temperature, humidity, supply_pressure, drain_pressure
                FROM sensor_logs
                WHERE layer_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (layer_id, start_time))
        else:
            cursor.execute("""
                SELECT 
                    datetime((strftime('%s', timestamp) / (? * 60)) * (? * 60), 'unixepoch') as timestamp,
                    ROUND(AVG(temperature), 1) as temperature,
                    ROUND(AVG(humidity), 1) as humidity,
                    ROUND(AVG(supply_pressure), 1) as supply_pressure,
                    ROUND(AVG(drain_pressure), 1) as drain_pressure
                FROM sensor_logs
                WHERE layer_id = ? AND timestamp >= ?
                GROUP BY datetime((strftime('%s', timestamp) / (? * 60)) * (? * 60), 'unixepoch')
                ORDER BY timestamp ASC
            """, (interval_minutes, interval_minutes, layer_id, start_time, interval_minutes, interval_minutes))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]

    return {
        'data': data,
        'aggregated': interval_minutes is not None,
        'interval_minutes': interval_minutes
    }

def select_images(layer_id=1, limit=100):
    """画像一覧を取得する"""
    parent_dir = Path(__file__).parent
    image_dir = parent_dir / 'plant_images' / f'layer_{layer_id}'
    
    if not image_dir.exists():
        return []

    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        image_files.extend(glob.glob(str(image_dir / ext)))
    
    images = []
    for file_path in image_files:
        filename = os.path.basename(file_path)
        try:
            date_str = filename.split('.')[0]
            timestamp = datetime.strptime(date_str, '%Y%m%d_%H%M%S').isoformat()
        except ValueError:
            mtime = os.path.getmtime(file_path)
            timestamp = datetime.fromtimestamp(mtime).isoformat()
        
        relative_path = f'plant_images/layer_{layer_id}/{filename}'
        images.append({'image_path': relative_path, 'timestamp': timestamp, 'filename': filename})
    
    images.sort(key=lambda x: x['timestamp'], reverse=True)
    return images[:limit]

def select_ai_reports(layer_id=1, limit=20):
    """AI解析レポート一覧を取得する"""
    with open_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT report_id, timestamp, image_path, growth_rate, 
                   ai_summary, ai_advice, llm_model_name
            FROM ai_reports
            WHERE layer_id = ? ORDER BY timestamp DESC LIMIT ?
        """, (layer_id, limit))
        return [dict(row) for row in cursor.fetchall()]

def select_logs(log_level=None, limit=100, offset=0):
    """システムログ一覧を取得する"""
    with open_db() as conn:
        cursor = conn.cursor()
        if log_level and log_level != 'ALL':
            cursor.execute("""
                SELECT log_id, timestamp, layer_id, log_level, message, details
                FROM system_logs WHERE log_level = ?
                ORDER BY timestamp DESC LIMIT ? OFFSET ?
            """, (log_level, limit, offset))
        else:
            cursor.execute("""
                SELECT log_id, timestamp, layer_id, log_level, message, details
                FROM system_logs ORDER BY timestamp DESC LIMIT ? OFFSET ?
            """, (limit, offset))
        return [dict(row) for row in cursor.fetchall()]

def select_schedules():
    """スケジュール一覧を取得する"""
    with open_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT schedule_id, layer_id, job_type, exec_time, is_enabled
            FROM schedules ORDER BY layer_id, job_type
        """)
        return [dict(row) for row in cursor.fetchall()]

def update_schedule(schedule_id, exec_time, is_enabled):
    """スケジュールを更新する"""
    if exec_time is None and is_enabled is None:
        raise ValueError('exec_time or is_enabled is required')

    with open_db() as conn:
        cursor = conn.cursor()
        update_fields = []
        params = []
        if exec_time is not None:
            update_fields.append('exec_time = ?')
            params.append(exec_time)
        if is_enabled is not None:
            update_fields.append('is_enabled = ?')
            params.append(1 if is_enabled else 0)
        params.append(schedule_id)
        
        query = f"UPDATE schedules SET {', '.join(update_fields)} WHERE schedule_id = ?"
        cursor.execute(query, params)

def toggle_schedule(schedule_id):
    """スケジュールの有効/無効を切り替える"""
    with open_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_enabled FROM schedules WHERE schedule_id = ?", (schedule_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        new_state = 0 if row['is_enabled'] else 1
        cursor.execute("UPDATE schedules SET is_enabled = ? WHERE schedule_id = ?", (new_state, schedule_id))
        return bool(new_state)

def process_ai_chat(user_message, image_filename, sensor_data):
    """AIチャットの応答を取得する"""
    if not gemini_model:
        raise ConnectionError('AI機能が無効です。LLM_API_KEYを設定してください。')

    system_prompt = create_system_prompt(sensor_data, image_filename)
    image_data = None
    if image_filename:
        try:
            parent_dir = Path(__file__).parent
            image_path = parent_dir / 'plant_images' / 'layer_1' / image_filename
            if image_path.exists():
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                image_data = Image.open(io.BytesIO(image_bytes))
            else:
                print(f"Warning: 画像ファイルが見つかりません: {image_path}")
        except Exception as e:
            print(f"画像読み込みエラー: {e}")

    try:
        if image_data:
            print(f"[AI Chat] 画像付きリクエスト: {user_message[:50]}...")
            response = gemini_model.generate_content([system_prompt + "\n\n" + user_message, image_data])
        else:
            print(f"[AI Chat] テキストリクエスト: {user_message[:50]}...")
            response = gemini_model.generate_content(system_prompt + "\n\n" + user_message)
        
        ai_response = response.text
        print(f"[AI Chat] レスポンス受信: {len(ai_response)}文字")
        return ai_response
    except Exception as e:
        error_msg = str(e)
        print(f"[AI Chat] Gemini API エラー: {error_msg}")
        if 'Timeout' in error_msg or 'DNS' in error_msg:
            raise ConnectionError('Gemini APIへの接続がタイムアウトしました。ネットワーク接続を確認してください。')
        elif '403' in error_msg or 'API key' in error_msg:
            raise ValueError('APIキーが無効です。設定を確認してください。')
        elif '429' in error_msg:
            raise ConnectionError('APIの使用制限に達しました。しばらく待ってから再試行してください。')
        else:
            raise RuntimeError(f'AI処理中にエラーが発生しました: {error_msg}')