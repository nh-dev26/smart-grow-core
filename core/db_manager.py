# core/db_manager.py

import sqlite3
import os
from datetime import datetime
import json

# DBファイルのパスは config.py から読み込む想定ですが、ここでは仮で定義します
DB_PATH = 'smart_grow_system.db'

# --- config.py から読み込む想定のデフォルト値 ---
# 初期データ投入に必要なため、config.pyがまだなくても、ここに一旦定義が必要です。
DEFAULT_SYSTEM_CONFIG = {
    "water_duration_sec": 10,
    "slack_webhook_url": "",
    "temp_alert_threshold": 30.0,
    "pump_gpio_sig": 17, # 仮のGPIO番号
    "dashboard_url": "http://your.funnel.url/dashboard",
    "low_threshold": 20.0 # tank_statusの初期値
}

DEFAULT_LAYERS = [
    (1, '1段目', '/dev/video0', 1), # layer_id, name, cam_id, is_active
]

DEFAULT_SCHEDULES = [
    (0, 'water', '12:00:00', 1), # layer_id=0 はシステム全体のジョブ
    (1, 'camera', '07:00:00', 1),
]

# --- 1. CREATE TABLE クエリの定義 ---
def get_create_table_queries():
    # 確定した6テーブル分のクエリを定義します
    return [
        # layers テーブル
        """
        CREATE TABLE IF NOT EXISTS layers (
            layer_id INTEGER PRIMARY KEY,
            layer_name TEXT NOT NULL,
            cam_id TEXT NOT NULL,
            is_active BOOLEAN NOT NULL
        );
        """,
        # schedules テーブル
        """
        CREATE TABLE IF NOT EXISTS schedules (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer_id INTEGER,
            job_type TEXT NOT NULL,
            exec_time TEXT NOT NULL,
            is_enabled BOOLEAN NOT NULL,
            FOREIGN KEY (layer_id) REFERENCES layers (layer_id)
        );
        """,
        # sensor_logs テーブル
        """
        CREATE TABLE IF NOT EXISTS sensor_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer_id INTEGER,
            timestamp TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            FOREIGN KEY (layer_id) REFERENCES layers (layer_id)
        );
        """,
        # system_config テーブル
        """
        CREATE TABLE IF NOT EXISTS system_config (
            config_id INTEGER PRIMARY KEY,
            water_duration_sec INTEGER NOT NULL,
            slack_webhook_url TEXT,
            temp_alert_threshold REAL NOT NULL,
            pump_gpio_sig INTEGER NOT NULL,
            dashboard_url TEXT,
            last_modified TEXT NOT NULL
        );
        """,
        # ai_reports テーブル
        """
        CREATE TABLE IF NOT EXISTS ai_reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer_id INTEGER,
            timestamp TEXT NOT NULL,
            growth_rate REAL NOT NULL,
            ai_summary TEXT NOT NULL,
            ai_advice TEXT,
            image_path TEXT NOT NULL,
            FOREIGN KEY (layer_id) REFERENCES layers (layer_id)
        );
        """,
        # tank_status テーブル
        """
        CREATE TABLE IF NOT EXISTS tank_status (
            tank_id INTEGER PRIMARY KEY,
            percentage REAL NOT NULL,
            status TEXT NOT NULL,
            low_threshold REAL NOT NULL,
            pressure_gpio_sig INTEGER NOT NULL,
            last_checked TEXT NOT NULL
        );
        """,
        # system_logs テーブル
        """
        CREATE TABLE IF NOT EXISTS system_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            layer_id INTEGER NOT NULL,
            log_level TEXT NOT NULL,
            message TEXT NOT NULL
        );
        """
    ]

# --- 2. 初期化関数 ---
def init_db(db_path=DB_PATH):
    if not os.path.exists(db_path):
        print(f"データベース '{db_path}' を初期化中...")
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # A. 全テーブルを作成
            for query in get_create_table_queries():
                cursor.execute(query)
            
            # B. デフォルトデータ挿入
            # layers, schedules, system_config, tank_status の初期レコードを挿入
            
            # (1) layers
            cursor.executemany(
                "INSERT INTO layers (layer_id, layer_name, cam_id, is_active) VALUES (?, ?, ?, ?)",
                DEFAULT_LAYERS
            )

            # (2) schedules
            cursor.executemany(
                "INSERT INTO schedules (layer_id, job_type, exec_time, is_enabled) VALUES (?, ?, ?, ?)",
                DEFAULT_SCHEDULES
            )

            # (3) system_config
            now = datetime.now().isoformat()
            cfg = DEFAULT_SYSTEM_CONFIG
            cursor.execute(
                """
                INSERT INTO system_config (config_id, water_duration_sec, slack_webhook_url, temp_alert_threshold, pump_gpio_sig, dashboard_url, last_modified) 
                VALUES (1, ?, ?, ?, ?, ?, ?)
                """,
                (cfg['water_duration_sec'], cfg['slack_webhook_url'], cfg['temp_alert_threshold'], cfg['pump_gpio_sig'], cfg['dashboard_url'], now)
            )

            # (4) tank_status (初期は100%, Normal)
            cursor.execute(
                """
                INSERT INTO tank_status (tank_id, percentage, status, low_threshold, pressure_gpio_sig, last_checked) 
                VALUES (1, 100.0, 'Normal', ?, ?, ?)
                """,
                (cfg['low_threshold'], 27, now) # 仮のGPIO番号27
            )

            conn.commit()
            print("初期化とデフォルト設定の挿入が完了しました。")
            
        except sqlite3.Error as e:
            print(f"データベース初期化エラー: {e}")
            
        finally:
            if conn:
                conn.close()
    else:
        print(f"データベース '{db_path}' は既に存在します。初期化をスキップしました。")

def insert_sensor_log(temperature: float, humidity: float, layer_id: int = 0):
    """
    温湿度センサの値をセンサーログテーブル (sensor_logs) にレコードを挿入する。

    :param layer_id: イベントが発生した層ID 
    :param temperature: 測定された温度値
    :param humidity: 測定された湿度値
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO sensor_logs (layer_id, timestamp, temperature, humidity) 
            VALUES (?, ?, ?, ?)
            """,
            (layer_id, timestamp, temperature, humidity)
        )
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"センサーログ記録エラー: {e}")
    finally:
        if conn:
            conn.close()
            
            
def insert_system_log(layer_id: int, log_level: str, message: str, details: str = None):
    """
    システムログテーブル (system_logs) にレコードを挿入する。

    :param layer_id: イベントが発生した層ID (0: システム全体)
    :param log_level: ログの重要度 ('INFO', 'ERROR'など)
    :param message: ログの概要メッセージ
    :param details: 詳細情報 (スタックトレースなど)
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO system_logs (timestamp, layer_id, log_level, message, details) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (timestamp, layer_id, log_level, message, details)
        )
        conn.commit()
        
    except sqlite3.Error as e:
        # このエラー自体をログに記録することはできないので、コンソールに出力
        print(f"致命的なエラー: System Log記録中にDBエラーが発生しました: {e}")
        
    finally:
        if conn:
            conn.close()