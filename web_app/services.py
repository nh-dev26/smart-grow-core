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
from core.ai_manager import process_ai_chat as core_process_ai_chat


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

def select_images(layer_id=1, limit=100):
    """画像一覧を取得する"""
    # core パッケージの file_manager から関数をインポートして使用
    from core.file_manager import select_images as core_select_images
    return core_select_images(layer_id, limit)

def process_ai_chat(user_message, image_filename, sensor_data):
    """AIチャットの応答を取得する"""
    # core パッケージの ai_manager から関数をインポートして使用
    return core_process_ai_chat(user_message, image_filename, sensor_data)
