import random
import datetime
import time
import statistics
from database.db_manager import insert_system_log, insert_sensor_log, select_system_config
from config import DEFAULT_SYSTEM_CONFIG # 閾値を取得するため
from hardware.aht25_reader import read_aht_sensor

def execute_sensor_job(layer_id: int, num_readings: int = 5, sleep_time: float = 1.0):
    """
    指定された層 (layer_id) の温湿度データを読み込み、DBに記録し、アラートをチェックする。
    物理センサがないため、ここではダミー値を使用する。
    """
    try:
        temps = []
        hums = []
    
        # 1. I2Cバス番号を取得 (DBから取得する関数を想定)
        # 🚨 DB初期化後、system_configからI2Cバス番号を取得するようにしてください 🚨
        i2c_bus = 1 # 仮の値。実際はDBから読み込みます。  

        print(f"[SENSOR JOB] センサー値の {num_readings} 回測定を開始...")
        for i in range(num_readings):
            data = read_aht_sensor(i2c_bus) 
            
            if data:
                temps.append(data['temperature'])
                hums.append(data['humidity'])
            else:
                # 取得失敗時も、ログを記録して続行
                insert_system_log(
                    layer_id=layer_id, 
                    log_level='WARNING', 
                    message='Failed to read sensor data.', 
                    details=f'Attempt {i+1} failed.'
                )
            
            time.sleep(sleep_time)
            
        if not temps or not hums:
            error_msg = "センサーから有効な値を一度も取得できませんでした。"
            insert_system_log(
                layer_id=layer_id, 
                log_level='ERROR', 
                message=error_msg, 
                details='All sensor readings failed or returned None.'
            )
            print(f"[SENSOR JOB - ERROR] {error_msg}")
            return

        temperature = statistics.mean(temps)
        humidity = statistics.mean(hums)

        insert_sensor_log(layer_id, temperature, humidity)
        
        # 3. システム設定からアラート閾値を取得
        config = select_system_config()
        
        temp_high_threshold = config.get('temp_high_threshold', DEFAULT_SYSTEM_CONFIG['temp_high_threshold'])
        temp_low_threshold = config.get('temp_low_threshold', DEFAULT_SYSTEM_CONFIG['temp_low_threshold']) 
        
        # 4. アラートチェック
        if temperature > temp_high_threshold:
            # 高温アラート
            alert_msg = f"温度アラート: {temperature}℃ (高温閾値 {temp_high_threshold}℃ 超過)"
            insert_system_log(
                layer_id=layer_id, 
                log_level='CRITICAL', 
                message=alert_msg, 
                details=f'Current temp: {temperature}')
            print(f"[SENSOR JOB - CRITICAL ALERT] {alert_msg}")
        
        elif temperature < temp_low_threshold:
            # 【追加】低温アラート
            alert_msg = f"温度アラート: {temperature}℃ (低温閾値 {temp_low_threshold}℃ 未満)"
            insert_system_log(
                layer_id=layer_id, 
                log_level='CRITICAL', 
                message=alert_msg, 
                details=f'Current temp: {temperature}')
            print(f"[SENSOR JOB - CRITICAL ALERT] {alert_msg}")
         
        insert_system_log(
            layer_id=layer_id, 
            log_level='INFO', 
            message='Sensor data recorded successfully.', 
            details=f'Temp: {temperature}℃, Hum: {humidity}%')
        print(f"[SENSOR JOB] Layer {layer_id} のデータを記録しました。 (温: {temperature}℃, 湿: {humidity}%)")

    except Exception as e:
        insert_system_log(
            layer_id=layer_id, 
            log_level='ERROR', 
            message='Unexpected error during sensor job.', 
            details=str(e))
        print(f"[CRITICAL ERROR] Sensor job failed: {e}")