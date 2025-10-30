import random
import datetime
from database.db_manager import insert_system_log, insert_sensor_log, select_system_config
from config import DEFAULT_SYSTEM_CONFIG # 閾値を取得するためにconfigもインポート

def execute_sensor_job(layer_id: int):
    """
    指定された層 (layer_id) の温湿度データを読み込み、DBに記録し、アラートをチェックする。
    物理センサがないため、ここではダミー値を使用する。
    """
    try:
        # TODO: aht25_reader内の関数を使用して実際のセンサデータを取得する
        temperature = round(random.uniform(25.0, 32.0), 1) 
        humidity = round(random.uniform(50.0, 75.0), 1)     






        insert_sensor_log(layer_id, temperature, humidity)
        
        # 3. システム設定からアラート閾値を取得
        config = select_system_config()
        
        temp_high_threshold = config.get('temp_high_threshold', DEFAULT_SYSTEM_CONFIG['temp_high_threshold'])
        temp_low_threshold = config.get('temp_low_threshold', DEFAULT_SYSTEM_CONFIG['temp_low_threshold']) 
        
        # 4. アラートチェック
        if temperature > temp_high_threshold:
            # 高温アラート
            alert_msg = f"温度アラート: {temperature}℃ (高温閾値 {temp_high_threshold}℃ 超過)"
            insert_system_log(layer_id, 'CRITICAL', alert_msg, f'Current temp: {temperature}')
            print(f"[SENSOR JOB - CRITICAL ALERT] {alert_msg}")
        
        elif temperature < temp_low_threshold:
            # 【追加】低温アラート
            alert_msg = f"温度アラート: {temperature}℃ (低温閾値 {temp_low_threshold}℃ 未満)"
            insert_system_log(layer_id, 'CRITICAL', alert_msg, f'Current temp: {temperature}')
            print(f"[SENSOR JOB - CRITICAL ALERT] {alert_msg}")
         
        insert_system_log(layer_id, 'INFO', 'Sensor data recorded successfully.', f'Temp: {temperature}℃, Hum: {humidity}%')
        print(f"[SENSOR JOB] Layer {layer_id} のデータを記録しました。 (温: {temperature}℃, 湿: {humidity}%)")

    except Exception as e:
        insert_system_log(layer_id, 'ERROR', 'Unexpected error during sensor job.', str(e))
        print(f"[CRITICAL ERROR] Sensor job failed: {e}")