# core/db_manager.py
DB_PATH = 'smart_grow_system.db'

DEFAULT_SYSTEM_CONFIG = {
    "water_duration_sec": 10,
    "slack_webhook_url": "",
    "temp_high_threshold": 38.0,# 高温アラート閾値　仮設定
    "temp_low_threshold": 10.0,# 低温音アラート閾値　仮設定
    "pump_gpio_sig": 17, # 仮のGPIO番号
    "dashboard_url": "http://your.funnel.url/dashboard",
    "low_threshold": 20.0, # tank_statusの初期値
    "i2c_bus_num": 1 # AHTセンサーのI2Cバス番号デフォルト
}

DEFAULT_LAYERS = [
    (1, '1段目', 0, 1), # layer_id, name, cam_id, is_active
]

DEFAULT_SCHEDULES = [
    (0, 'water', '12:00:00', 1), # layer_id=0 はシステム全体のジョブ
    (0, 'sensor', '00:30:00', 1),
    (1, 'camera', '09:00:00', 1),
]

# hardware/aht25_reader.py
DEFAULT_I2C_BUS_NUM = 1

# jobs/camera_jobs.py
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720
RETENTION_DAYS = 90
BASE_SAVE_DIR = "plant_images" 

# hardware/aht25_reader.py
AHT_ADDRESS = 0x38
AHT_TRIGGER_CMD = [0xAC, 0x33, 0x00]