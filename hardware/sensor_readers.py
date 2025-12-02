import time
import errno
import random
import platform

# --- smbus2を安全にインポート ---
try:
    import smbus2
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False

from config import AHT_ADDRESS, AHT_TRIGGER_CMD
    
def read_aht_sensor(i2c_bus_num=1):
    """
    AHT25/AHT20センサーから温湿度データを1回取得し、辞書で返す。
    """
    simulate = False
    if not SMBUS_AVAILABLE or platform.system() != "Linux":
        simulate = True

    if simulate:
        print("AHT Sensor Simulation Mode: 実機ではありません。")
        return {"temperature": 23.5, "humidity": 45.2}

    try:
        i2c = smbus2.SMBus(i2c_bus_num)
        
        # 1. 初期化コマンドの送信
        i2c.write_i2c_block_data(AHT_ADDRESS, 0xBE, [0x08, 0x00])
        time.sleep(0.2)
        
        # 2. 測定トリガコマンド送信
        i2c.write_i2c_block_data(AHT_ADDRESS, AHT_TRIGGER_CMD[0], AHT_TRIGGER_CMD[1:])
        time.sleep(0.08)
        
        # 3. データの読み込み
        try:
            # 7バイトのデータを純粋なReadで取得
            read_msg = smbus2.i2c_msg.read(AHT_ADDRESS, 7)
            i2c.i2c_rdwr(read_msg)
            data = list(read_msg)
        except OSError as e:
            if e.errno == errno.EREMOTEIO:
                time.sleep(0.1)
                read_msg = smbus2.i2c_msg.read(AHT_ADDRESS, 7)
                i2c.i2c_rdwr(read_msg)
                data = list(read_msg)
            else:
                raise
        
        # 4. データ変換と物理量計算

        # 湿度 (RH) - 20ビット
        hum_raw = (data[1] << 12) | (data[2] << 4) | (data[3] >> 4)
        humidity = (hum_raw * 100.0) / 1048576.0
        
        # 温度 (℃) - 20ビット
        temp_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
        temperature = (temp_raw * 200.0) / 1048576.0 - 50
        
        return {
            "temperature": round(temperature, 2), 
            "humidity": round(humidity, 2)
        }
            
    except FileNotFoundError:
        print("AHT Sensor Error: I2Cバスが見つかりません。")
        return None
    except Exception as e:
        print(f"AHT Sensor Error: 読み取り中に予期せぬエラーが発生しました: {e}")
        return None
    finally:
        try:
            if 'i2c' in locals() and i2c:
                i2c.close()
        except:
            pass
    
    
def read_pressure_sensor(sim_name: str) -> float | None:
    """
    水圧センサー（MS5837）のダミー値を返す。
    :param sim_name: センサーの識別名 ('Supply' または 'Drain')
    :return: 圧力値 (mbar, float) または None
    """

    # --- 以下はダミーモードの動作 ---
    if random.randint(1, 10) == 1:
        print(f"{sim_name} Pressure Sensor Simulation: 読み取りエラー（Noneを返します）")
        return None
    
    dummy_pressure = random.uniform(1013.0, 1062.0)
    return round(dummy_pressure, 2)

def read_supply_pressure() -> float | None:
    """
    給水タンクの水圧/水位を読み取るダミー関数。
    """
    return read_pressure_sensor("Supply")

def read_drain_pressure() -> float | None:
    """
    排水タンクの水圧/水位を読み取るダミー関数。
    """
    return read_pressure_sensor("Drain")