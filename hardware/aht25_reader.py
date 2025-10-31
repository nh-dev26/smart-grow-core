import smbus2
import time

i2c = smbus2.SMBus(1)
address = 0x38

i2c.write_i2c_block_data(address, 0xBE, [0x08, 0x00])
time.sleep(0.2)

i2c.write_i2c_block_data(address, 0xAC, [0x33, 0x00])

time.sleep(0.5)  
try:
    data = i2c.read_i2c_block_data(address, 0x00, 6)
except OSError as e:
    if e.errno == 121:

        time.sleep(0.1)
        data = i2c.read_i2c_block_data(address, 0x00, 6)

hum = ((data[1] << 12) | (data[2] << 4) | (data[3] >> 4)) * 100 / 1048576.0
temp = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]) * 200 / 1048576.0 - 50

print(f"Humidity: {hum:.2f} %")
print(f"Temperature: {temp:.2f} c")

