from time import sleep
from datetime import datetime
from database.db_manager import select_system_config

# --- gpiozero を安全にインポート ---
try:
    from gpiozero import OutputDevice
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False


def execute_pump_job(layer_id: int, duration: int = 5):
    """
    水ポンプ制御ジョブ。
    指定された層(layer_id)のポンプを一定時間ONにしてOFFにする。
    """
    print(f"[{datetime.now()}] [WATER JOB START] Layer {layer_id} の水ポンプ制御を開始します。")

    # TODO:水圧センサ水完成後安全確認ロジックを追加 （給水、排水タンクの確認）
    # 例:
    # if tank_is_full():
    #     print("[WATER JOB] 排水タンクが満タンのため中止しました。")
    #     return

    config = select_system_config() or {}
    pump_pin = config.get("pump_gpio_pin", 17) 

    if not GPIO_AVAILABLE:
        print("[INFO] GPIOライブラリが利用できない環境です。ダミーモードで動作します。")
        print("[DUMMY] 5秒間ポンプON → OFF（実際の制御は行われません）")
        sleep(duration)
        print("[DUMMY] ポンプOFF完了。")
        return
    
    try:
        pump = OutputDevice(pump_pin, active_high=False, initial_value=True)
        # ポンプをON（リレーLOW出力）
        pump.off()
        print(f"[WATER JOB] ポンプを {duration} 秒間動作させます。")
        sleep(duration)
    except Exception as e:
        print(f"[WATER JOB ERROR] {e}")
    finally:
        # ポンプを確実にOFFに
        pump.on()
        print(f"[{datetime.now()}] [WATER JOB END] Layer {layer_id} のポンプ制御を終了しました。")

if __name__ == "__main__":
    # テスト実行
    execute_pump_job(layer_id=1, duration=5)