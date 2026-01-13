import random
import datetime
import time
import statistics
from database.db_manager import insert_system_log, insert_sensor_log, select_system_config, select_i2c_bus_num
from config import DEFAULT_SYSTEM_CONFIG # 閾値を取得するため
from hardware.sensor_readers import read_aht_sensor, read_supply_pressure, read_drain_pressure, get_water_level_api_data

def execute_sensor_job(layer_id: int, num_readings: int = 5, sleep_time: float = 1.0):
    try:
        temps, hums, supply_pressures, drain_pressures = [], [], [], []
        i2c_bus = select_i2c_bus_num()
      
        print(f"[SENSOR JOB] センサー値の {num_readings} 回測定を開始...")
        for i in range(num_readings):
            data_aht = read_aht_sensor(i2c_bus) 
            water_data = get_water_level_api_data()
            
            if data_aht:
                temps.append(data_aht['temperature'])
                hums.append(data_aht['humidity'])
            
            s_val, d_val = None, None
            if water_data and water_data.get("ok"):
                s_val = water_data.get("supply_mm")
                d_val = water_data.get("drain_mm")
                if s_val is not None: supply_pressures.append(s_val)
                if d_val is not None: drain_pressures.append(d_val)
            
            if not data_aht or s_val is None or d_val is None:
                failed = [n for n, v in [("AHT", data_aht), ("Supply", s_val), ("Drain", d_val)] if v is None]
                insert_system_log(layer_id, 'WARNING', 'Sensor partial failure', f'Attempt {i+1} failed for: {", ".join(failed)}')
            
            time.sleep(sleep_time)
            
        # 統計（平均）の算出
        temperature = round(statistics.mean(temps), 2) if temps else None
        humidity = round(statistics.mean(hums), 2) if hums else None
        avg_supply_dist = round(statistics.mean(supply_pressures), 2) if supply_pressures else None
        avg_drain_dist = round(statistics.mean(drain_pressures), 2) if drain_pressures else None

        # 設定の取得
        config = select_system_config()
        s_full_dist = config.get('supply_low_threshold', DEFAULT_SYSTEM_CONFIG['supply_low_threshold'])
        d_full_dist = config.get('drain_high_threshold', DEFAULT_SYSTEM_CONFIG['drain_high_threshold'])
        
        # --- 水位・残量計算 (ゼロ除算防止) ---
        supply_percent = None
        if avg_supply_dist is not None and s_full_dist and s_full_dist > 0:
            supply_level_mm = max(0, s_full_dist - avg_supply_dist)
            supply_percent = round((supply_level_mm / s_full_dist) * 100, 1)

        drain_percent = None
        if avg_drain_dist is not None and d_full_dist and d_full_dist > 0:
            drain_level_mm = max(0, d_full_dist - avg_drain_dist)
            drain_percent = round((drain_level_mm / d_full_dist) * 100, 1)

        # センサーログの保存（計算後の％を保存）
        insert_sensor_log(layer_id, temperature, humidity, 
                          supply_pressure=supply_percent, 
                          drain_pressure=drain_percent)
   
        # --- 温度アラートチェック ---
        temp_high = config.get('temp_high_threshold', DEFAULT_SYSTEM_CONFIG['temp_high_threshold'])
        temp_low = config.get('temp_low_threshold', DEFAULT_SYSTEM_CONFIG['temp_low_threshold']) 
        
        if temperature is not None:
            if temperature > temp_high:
                insert_system_log(layer_id, 'CRITICAL', f"高温アラート: {temperature}℃", f'High threshold: {temp_high}')
            elif temperature < temp_low:
                insert_system_log(layer_id, 'CRITICAL', f"低温アラート: {temperature}℃", f'Low threshold: {temp_low}')
         
        # 完了ログの作成
        log_level = 'INFO'
        log_message = 'Sensor data recorded successfully.'
        if all(v is None for v in [temperature, humidity, supply_percent, drain_percent]):
            log_level = 'ERROR' 
            log_message = 'All sensor readings failed.'

        insert_system_log(
            layer_id=layer_id, log_level=log_level, message=log_message,
            details=f'Temp: {temperature}, Hum: {humidity}, Supply: {supply_percent}%, Drain: {drain_percent}%'
        )
        print(f"[SENSOR JOB] Layer {layer_id} 記録完了 (温: {temperature}℃, 湿: {humidity}%, 給水: {supply_percent}%, 排水: {drain_percent}%)")
  
    except Exception as e:
        insert_system_log(layer_id, 'ERROR', 'Unexpected error during sensor job.', str(e))
        print(f"[CRITICAL ERROR] Sensor job failed: {e}")