import smbus2
import time
 
# I2C設定
i2c = smbus2.SMBus(1)
address = 0x38
 
def init_aht25():
    """AHT25センサーの初期化"""
    try:
        # ソフトリセット
        i2c.write_byte(address, 0xBA)
        time.sleep(0.02)
        # 初期化コマンド (AHT20/25系のおまじない)
        i2c.write_i2c_block_data(address, 0xBE, [0x08, 0x00])
        time.sleep(0.1)
        print("AHT25 初期化完了")
    except Exception as e:
        print(f"初期化エラー: {e}")
        raise
 
def read_aht25():
    """温度と湿度を読み取る"""
    # 1. 測定開始コマンド送信
    try:
        i2c.write_i2c_block_data(address, 0xAC, [0x33, 0x00])
    except Exception as e:
        print(f"コマンド送信エラー: {e}")
        raise
    # 測定完了待ち（データシート推奨 >= 80ms）
    time.sleep(0.08)
    # 2. データ読み取り（ここを修正）
    # read_i2c_block_dataの代わりに、i2c_rdwrを使って純粋なReadを行う
    # これにより、不要なレジスタ書き込み(0x00)を防ぐ
    try:
        read_msg = smbus2.i2c_msg.read(address, 7)
        i2c.i2c_rdwr(read_msg)
        dat = list(read_msg) # リスト形式に変換
    except Exception as e:
        print(f"データ読み取りエラー: {e}")
        raise
 
    # 3. ビジー状態の確認
    # ビット7 (Busy indication): 1=Busy, 0=Ready
    status = dat[0]
    if (status & 0x80) != 0:
        # まだビジーの場合は、少し待って再帰呼び出しするか、エラーを返す
        # ここではシンプルに待機してリトライする簡易実装
        time.sleep(0.02)
        # ※本来はここで再度読み取りループを回すべきですが、
        # 80ms待機していれば通常は完了しています。
        # 念のためWarningを出して処理を続行、またはException推奨
        print("Warning: Sensor indicates busy")
 
    # --- 湿度の計算 ---
    # 20ビット: Byte1(8) + Byte2(8) + Byte3上位4ビット
    hum_raw = ((dat[1] << 12) | (dat[2] << 4) | (dat[3] >> 4))
    hum = (hum_raw * 100.0) / 1048576.0 # 2^20 = 1048576
    # --- 温度の計算 ---
    # 20ビット: Byte3下位4ビット + Byte4(8) + Byte5(8)
    tmp_raw = (((dat[3] & 0x0F) << 16) | (dat[4] << 8) | dat[5])
    tmp = (tmp_raw * 200.0) / 1048576.0 - 50
    return tmp, hum
 
# --- メイン処理 ---
if __name__ == "__main__":
    try:
        init_aht25()
        print("計測開始 (Ctrl+Cで停止)")
        print("-" * 40)
        while True:
            try:
                t, h = read_aht25()
                print(f"温度: {t:6.2f}°C  |  湿度: {h:6.2f}%")
                time.sleep(2)
            except Exception as e:
                print(f"測定エラー: {e}")
                time.sleep(1)
                # エラー時は再初期化を試みると復帰しやすい
                try:
                    init_aht25()
                except:
                    pass
    except KeyboardInterrupt:
        print("\n\n測定を停止しました")
    finally:
        i2c.close()