import sqlite3
import os
from datetime import datetime
import json
from config import *

def get_create_table_queries():
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
            message TEXT NOT NULL,
            details TEXT
        );
        """
    ]

def init_db(db_path=DB_PATH):
    """
    データベースファイルが存在しない場合、初期化して必要なテーブルを作成し、デフォルト設定を挿入する。

    :param db_path: データベースファイルのパス
    """
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


def insert_camera_log(layer_id: int, image_path: str):
    """ai_reports テーブルに画像パスと仮のAIデータを記録する。"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()

        # growth_rate, ai_summary は Webアプリ/AI機能が未実装のため仮の値 ('N/A')
        cursor.execute(
            """
            INSERT INTO ai_reports (layer_id, timestamp, growth_rate, ai_summary, ai_advice, image_path) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            # layer_idはデフォルト値を持たず、ジョブから渡される想定
            (layer_id, timestamp, 0.0, 'N/A', '', image_path)
        )
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"カメラログ記録エラー: {e}")
        # DBログ記録失敗自体は system_logs に記録できないため、コンソールに出力
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
            
def select_layer_info(layer_id: int):
    """
    指定された層 (layer_id) の設定情報を取得する。

    :param layer_id: 取得したい層のID
    :return: 層の設定を格納した辞書 (レコードが見つからない場合は None)
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # layer_idに基づいてlayersテーブルから情報を取得
        cursor.execute("SELECT * FROM layers WHERE layer_id = ?", (layer_id,))
        
        # データベースからカラム名を取得
        columns = [description[0] for description in cursor.description]
        
        # 結果を辞書形式で取得
        result = cursor.fetchone()
        
        if result:
            # カラム名と値を結合して辞書を返す
            layer_info = dict(zip(columns, result))
            return layer_info
        else:
            return None
            
    except sqlite3.Error as e:
        print(f"層情報取得エラー: {e}")
        # システムログは使えないため、コンソールに出力
        return None
    finally:
        if conn:
            conn.close()
            
    
def select_schedules():
    """
    schedulesテーブルから有効な（is_enabled=1）ジョブスケジュールをすべて取得する。

    :return: スケジュールレコードのリスト。各要素は辞書形式。
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        # 結果を辞書形式 (カラム名: 値) で取得できるように設定
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()

        # is_enabled が 1 の（有効な）スケジュールのみを取得
        cursor.execute("SELECT * FROM schedules WHERE is_enabled = 1")
        
        # 取得した行をすべて辞書に変換して返す
        schedules = [dict(row) for row in cursor.fetchall()]
        return schedules
            
    except sqlite3.Error as e:
        print(f"スケジュール情報取得エラー: {e}")
        # エラー発生時は空のリストを返す
        return []
    finally:
        if conn:
            conn.close()