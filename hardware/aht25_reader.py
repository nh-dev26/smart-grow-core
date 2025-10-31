import smbus2
import time
import errno # OSErrorのerrnoを扱うためにインポート
from config import AHT_ADDRESS, AHT_TRIGGER_CMD

def read_aht_sensor(i2c_bus_num=1):
    """
    AHT25/AHT20センサーから温湿度データを1回取得し、辞書で返す。
    
    Args:
        i2c_bus_num (int): I2Cバスの番号 (デフォルト: 1)
        
    Returns:
        dict: {"temperature": T, "humidity": H} のデータ, または None
    """
    try:
        # I2Cバスに接続
        i2c = smbus2.SMBus(i2c_bus_num)
        
        # 1. 初期化コマンドの送信 (0xBE, 0x08, 0x00)
        # これはセンサーのキャリブレーションやステータス設定を行うためのコマンドです
        i2c.write_i2c_block_data(AHT_ADDRESS, 0xBE, [0x08, 0x00])
        time.sleep(0.2)
        
        # 2. 測定トリガコマンド送信 (0xAC, 0x33, 0x00)
        i2c.write_i2c_block_data(AHT_ADDRESS, 0xAC, [0x33, 0x00])
        time.sleep(0.5) # 測定完了を待機
        
        # 3. データの読み込み
        try:
            # 6バイトのデータを読み込む (Status, RH_H, RH_M, RH_L/Temp_H, Temp_M, Temp_L)
            data = i2c.read_i2c_block_data(AHT_ADDRESS, 0x00, 6)
        except OSError as e:
            # エラー121 (Remote I/O error) は、センサーがまだ準備できていない可能性があるため再試行
            if e.errno == errno.EREMOTEIO: # EREMOTEIO は通常 121
                time.sleep(0.1)
                data = i2c.read_i2c_block_data(AHT_ADDRESS, 0x00, 6)
            else:
                raise # その他のOSErrorは再スロー
                
        # 4. データ変換と物理量計算

        hum_raw = (data[1] << 12) | (data[2] << 4) | (data[3] >> 4)
        humidity = hum_raw * 100 / 1048576.0 # 2^20 = 1048576.0
        
        # 温度 (℃)
        temp_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
        temperature = temp_raw * 200 / 1048576.0 - 50
        
        return {
            "temperature": round(temperature, 2), 
            "humidity": round(humidity, 2)
        }
            
    except FileNotFoundError:
        print("AHT Sensor Error: I2Cバスが見つかりません。I2Cが有効か確認してください。")
        return None
    except Exception as e:
        print(f"AHT Sensor Error: 読み取り中に予期せぬエラーが発生しました: {e}")
        return None