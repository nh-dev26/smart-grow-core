import smbus2
import time

# I2C設定
i2c = smbus2.SMBus(1)
address = 0x38

#トリガ設定コマンド
set = [0xAC, 0x33, 0x00]

#データ読み込み用
dat = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

# DHT20/AHT25設定
time.sleep(0.1)
ret = i2c.read_byte_data(address, 0x71)

# if ret != 0x18:
    # initialization process


# トリガ測定コマンド送信
time.sleep(0.01)
i2c.write_i2c_block_data(address, 0x00, set)

# データの読み込み
time.sleep(0.08)
dat = i2c.read_i2c_block_data(address, 0x00, 0x07)

# データ変換
hum = dat[1] << 12 | dat[2] << 4 | ((dat[3] & 0xF0) >> 4)
tmp = ((dat[3] & 0x0F) << 16) | dat[4] << 8 | dat[5]

# 物理量変換
hum = hum / 2**20 * 100
tmp = tmp / 2**20 * 200 - 50

# 表示
print("hum: " + str(hum))
print("tmp: " + str(tmp))
    
    
    
