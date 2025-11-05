import random
import datetime
import time
import statistics
from database.db_manager import insert_system_log, insert_sensor_log, select_system_config, select_i2c_bus_num
from config import DEFAULT_SYSTEM_CONFIG # 閾値を取得するため
from hardware.sensor_readers import read_aht_sensor, read_supply_pressure, read_drain_pressure

def execute_sensor_job(layer_id: int, num_readings: int = 5, sleep_time: float = 1.0):
    """
    指定された層 (layer_id) の温湿度データを読み込み、DBに記録し、アラートをチェックする。
    物理センサがないため、ここではダミー値を使用する。
    """
    try:
        temps = []
        hums = []
        supply_pressures = []
        drain_pressures = []
        
        i2c_bus = select_i2c_bus_num()
      
        print(f"[SENSOR JOB] センサー値の {num_readings} 回測定を開始...")
        for i in range(num_readings):
            data = read_aht_sensor(i2c_bus) 
            supply_pressure = read_supply_pressure()
            drain_pressure = read_drain_pressure()
            
           # 温湿度
            if data:
                temps.append(data['temperature'])
                hums.append(data['humidity'])
            
            # 給水圧
            if supply_pressure is not None:
                supply_pressures.append(supply_pressure)
            
            # 排水圧
            if drain_pressure is not None:
                drain_pressures.append(drain_pressure)
                
            #  警告ログ: いずれかの取得失敗時はシステムログに記録
            if not data or supply_pressure is None or drain_pressure is None:
                failure_details = []
                if not data: failure_details.append("AHT")
                if supply_pressure is None: failure_details.append("SupplyPressure")
                if drain_pressure is None: failure_details.append("DrainPressure")
                
                insert_system_log(
                    layer_id=layer_id, 
                    log_level='WARNING', 
                    message='Failed to read some sensor data.', 
                    details=f'Attempt {i+1} failed for: {", ".join(failure_details)}.'
                )
            
            time.sleep(sleep_time)
            
        temperature = round(statistics.mean(temps), 2) if temps else None
        humidity = round(statistics.mean(hums), 2) if hums else None
        
        avg_supply_pressure = round(statistics.mean(supply_pressures), 2) if supply_pressures else None
        avg_drain_pressure = round(statistics.mean(drain_pressures), 2) if drain_pressures else None

        insert_sensor_log(layer_id, temperature, humidity, supply_pressure=avg_supply_pressure, drain_pressure=avg_drain_pressure)
        
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
            # 低温アラート
            alert_msg = f"温度アラート: {temperature}℃ (低温閾値 {temp_low_threshold}℃ 未満)"
            insert_system_log(
                layer_id=layer_id, 
                log_level='CRITICAL', 
                message=alert_msg, 
                details=f'Current temp: {temperature}')
            print(f"[SENSOR JOB - CRITICAL ALERT] {alert_msg}")
         
        log_level = 'INFO'
        log_message = 'Sensor data recorded successfully.'

        # 全てのデータが欠損していた場合に log_level を ERROR に変更
        if temperature is None and humidity is None and avg_supply_pressure is None and avg_drain_pressure is None:
            log_level = 'ERROR' 
            log_message = 'All sensor readings failed. Recorded NULL for all sensor data.'
            print(f"[SENSOR JOB - ERROR] {log_message}")
        # 正常終了ログ
        insert_system_log(
            layer_id=layer_id, 
            log_level=log_level,  
            message=log_message,
            details=f'Temp: {temperature}℃, Hum: {humidity}%, SupplyP: {avg_supply_pressure}, DrainP: {avg_drain_pressure}'
        )
        print(f"[SENSOR JOB] Layer {layer_id} のデータを記録しました。 (温: {temperature}℃, 湿: {humidity}%, 給水圧: {avg_supply_pressure}, 排水圧: {avg_drain_pressure})")
  
    except Exception as e:
        insert_system_log(
            layer_id=layer_id, 
            log_level='ERROR', 
            message='Unexpected error during sensor job.', 
            details=str(e))
        print(f"[CRITICAL ERROR] Sensor job failed: {e}")