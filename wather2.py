import lgpio
import time

PUMP_PIN = 17   # BCM17

# �f�t�H���g gpiochip0 ���g��
h = lgpio.gpiochip_open(0)

# �o�͂Ŏg�p�iACTIVE_LOW�Ȃ̂� 1=OFF, 0=ON�j
lgpio.gpio_claim_output(h, PUMP_PIN, 0)

print("�|���v ON�i5�b�j")
lgpio.gpio_write(h, PUMP_PIN, 1)  # LOW = ON
time.sleep(5)

print("�|���v OFF")
lgpio.gpio_write(h, PUMP_PIN, 0)  # HIGH = OFF

# ��Еt��
lgpio.gpiochip_close(h)
