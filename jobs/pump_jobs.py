from time import sleep
from datetime import datetime
from database.db_manager import select_system_config, insert_system_log

try:
    import lgpio
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False


def execute_pump_job(layer_id: int):
 
    config = select_system_config() or {}
    pump_pin = config.get("pump_gpio_sig", 17)
    duration = config.get("water_duration_sec", 10)

    print(f"[{datetime.now()}] [WATER JOB START] Layer {layer_id}")

    insert_system_log(
        layer_id=layer_id,
        log_level='INFO',
        message='Pump job started.',
        details=f"GPIO Pin: {pump_pin}, Duration: {duration}s"
    )

    if not GPIO_AVAILABLE:
        print("[INFO] GPIO���g���Ȃ����߃_�~�[���[�h�œ��삵�܂�")
        sleep(duration)
        return

    h = None

    try:
        # GPIO�`�b�v���I�[�v��
        h = lgpio.gpiochip_open(0)

        # �o�͂Ƃ��Ċm�ہi������ԁFOFF = HIGH�j
        lgpio.gpio_claim_output(h, pump_pin, 0)

        # �|���vON�iActive Low�j
        lgpio.gpio_write(h, pump_pin, 1)
        print(f"[WATER JOB] �|���vON�i{duration}�b�j")
        sleep(duration)

        insert_system_log(
            layer_id=layer_id,
            log_level='INFO',
            message='Pump job completed successfully.',
            details='Pump operated and will be turned OFF.'
        )

    except Exception as e:
        print(f"[WATER JOB ERROR] {e}")
        insert_system_log(
            layer_id=layer_id,
            log_level='CRITICAL',
            message='Error occurred during pump job.',
            details=f'Pump job failed: {e}'
        )

    finally:
        if h is not None:
            # �m���Ƀ|���vOFF
            try:
                lgpio.gpio_write(h, pump_pin, 0)
            except Exception:
                pass

            lgpio.gpiochip_close(h)

        print(f"[{datetime.now()}] [WATER JOB END] Layer {layer_id}")

        insert_system_log(
            layer_id=layer_id,
            log_level='INFO',
            message='Pump job process terminated.',
            details='Pump OFF completed and GPIO released.'
        )


if __name__ == "__main__":
    execute_pump_job(layer_id=1)