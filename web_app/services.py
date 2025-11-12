# web_app/services.py

from datetime import datetime, timedelta
import random

def get_latest_sensor_data():
    """
    ダミーの最新センサーデータを取得する（実際はdatabase/coreモジュールから取得）
    """
    now_utc = datetime.utcnow().isoformat() + 'Z'
    return {
        "temperature": round(25.0 + random.uniform(-1.5, 1.5), 1),
        "humidity": random.randint(60, 80),
        "supply_pressure": round(90.0 + random.uniform(-10.0, 5.0), 1), # 70〜95 kPa
        "drain_pressure": round(130.0 + random.uniform(-15.0, 30.0), 1), # 115〜160 kPa
        "timestamp": now_utc
    }

def get_next_schedules():
    """
    ダミーの次回スケジュールを取得する（実際はjobsモジュールから取得）
    """
    return [
        {"job_type": "water", "layer_id": 1, "exec_time": (datetime.now() + timedelta(minutes=30)).strftime('%H:%M')},
        {"job_type": "camera", "layer_id": 2, "exec_time": (datetime.now() + timedelta(hours=1)).strftime('%H:%M')},
    ]

def get_recent_alerts():
    """
    ダミーの最近のアラートを取得する（実際はlogsモジュールなどから取得）
    """
    now = datetime.now()
    return [
        {"log_level": "WARNING", "layer_id": 1, "message": "給水圧が低めです", "timestamp": (now - timedelta(minutes=5)).isoformat() + 'Z'},
        {"log_level": "INFO", "layer_id": 3, "message": "定期センサー測定完了", "timestamp": (now - timedelta(minutes=10)).isoformat() + 'Z'},
    ]

def get_latest_image():
    """
    ダミーの最新画像情報を取得する
    """
    return {
        "image_path": "static/img/dummy_plant.jpg", # web_app/static/img/dummy_plant.jpg を想定
        "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat() + 'Z'
    }

def get_dashboard_data():
    """
    ダッシュボード用の全データを集約するメイン関数
    """
    return {
        "success": True,
        "sensor_data": get_latest_sensor_data(),
        "latest_image": get_latest_image(),
        "next_schedules": get_next_schedules(),
        "alerts": get_recent_alerts()
    }