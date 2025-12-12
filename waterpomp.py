from gpiozero import OutputDevice
from time import sleep

# リレー制御に使用するGPIOピン番号 (BCMモード)
PUMP_PIN = 17 

# リレーモジュール AE-G5V-DRVは、信号 LOW (0V) でコイルが動作（ON）するタイプが多いです。
# そのため、active_high=False を指定します。

# initial_value=True は、プログラム開始時にピンをHIGHにして、リレーを確実にOFF (ポンプ停止) にします。
try:
    # OutputDeviceを初期化。 LOWでONになるように設定
    pump_relay = OutputDevice(PUMP_PIN, active_high=False, initial_value=True) 

    print("--- 水ポンプ制御を開始 ---")
    print(f"GPIO BCM {PUMP_PIN} を使用してリレーを制御します。")
    print("現在の状態: ポンプ停止中")
    
    # 5秒間ポンプを動作させる
    print("\n[動作開始] ポンプを 5秒間 ON にします...")
    pump_relay.off()  # active_high=False なので、.off()でLOW (ON信号) が出力されます
    
    sleep(10)  # 5秒間待機

    # ポンプを停止させる
    print("[動作停止] ポンプを OFF にします。")
    pump_relay.on()   # active_high=False なので、.on()でHIGH (OFF信号) が出力されます
    
    print("\n制御が完了しました。")

except KeyboardInterrupt:
    print("\nユーザーによる終了操作が検出されました。")
    
finally:
    # 終了時に必ずリレーをOFFにし、ピンの状態をクリーンアップします
    pump_relay.on() 
    print("GPIOピンを解放し、プログラムを終了します。")
    
    
    
    
# 接続元,接続先,備考
# Raspberry Pi (RPi) BCM 17,リレーモジュール IN/SIG,制御信号（ON/OFF）を送る
# RPi GND,リレーモジュール GND,信号系のGND接続（共通化）
# RPi 5V,リレーモジュール VCC,リレーのコイルを駆動するための電源 BCM2?
# **12V外部電源 (+) **,リレーモジュールの COM (共通),ポンプ駆動用の電力供給元
# **12V外部電源 (-) **,**水中ポンプ (-) **,ポンプ駆動回路のGND
# **水中ポンプ (+) **,リレーモジュールの NO (常時開),ポンプのON/OFFを行う接点