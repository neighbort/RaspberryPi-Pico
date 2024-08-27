from machine import Pin, I2C, deepsleep
import time
from ssd1306 import SSD1306_I2C

# Set up Display
WIDTH  = 128
HEIGHT = 64
i2c_disp = I2C( 0, scl=Pin(5), sda=Pin(4) )
i2c_disp.scan()
oled = SSD1306_I2C( WIDTH, HEIGHT, i2c_disp )

# Set up MMA8452
i2c_mma8452 = I2C( 1, scl=Pin(27), sda=Pin(26) )
print(hex(i2c_mma8452.scan()[0]))
MMA8452_ADDR = 0x1c		# write value of hex(i2c_mma8452.scan()[0])
REG_WHO_AM_I = 0x0D
REG_CTRL_REG1 = 0x2A
REG_XYZ_DATA_CFG = 0x0E
REG_CTRL_REG2 = 0x2B
REG_OUT_X_MSB = 0x01
i2c_mma8452.writeto_mem(MMA8452_ADDR, REG_CTRL_REG1, b'\x01')

# Set up Low Pass Filter
alpha = 0.8  # フィルタ係数, 0~1.0
x_filtered, y_filtered, z_filtered = 0, 0, 0

# Set up Display
WIDTH  = 128
HEIGHT = 64
i2c_disp = I2C( 0, scl=Pin(5), sda=Pin(4) )
i2c_disp.scan()
oled = SSD1306_I2C( WIDTH, HEIGHT, i2c_disp )

### DEFINE FUNCTION ###
# Get mma8452 value
def read_acceleration(i2c, MMA8452_ADDRESS, REG_OUT_X_MSB):
    global x_filtered, y_filtered, z_filtered
    # データの読み取り
    data = i2c.readfrom_mem(MMA8452_ADDRESS, REG_OUT_X_MSB, 6)
    # 16ビットの加速度データを取得
    x = (data[0] << 8 | data[1]) >> 4
    y = (data[2] << 8 | data[3]) >> 4
    z = (data[4] << 8 | data[5]) >> 4
    # 12ビットのデータを符号拡張
    if x > 2047:
        x -= 4096
    if y > 2047:
        y -= 4096
    if z > 2047:
        z -= 4096
    # 加速度をgに変換
    x = x / 1024
    y = y / 1024
    z = z / 1024
    # Apply Low Pass Filter
    x_filtered = alpha * x + (1 - alpha) * x_filtered
    y_filtered = alpha * y + (1 - alpha) * y_filtered
    z_filtered = alpha * z + (1 - alpha) * z_filtered
    #return x, y, z
    return x_filtered, y_filtered, z_filtered

# Main Roop
while True:
    x, y, z = read_acceleration(i2c_mma8452, MMA8452_ADDR, REG_OUT_X_MSB)
    valuex = "X=" + str(x) + "g"
    valuey = "Y=" + str(y) + "g"
    valuez = "Z=" + str(z) + "g"
    oled.init_display()
    oled.text( valuex, 5, 5 )
    oled.text( valuey, 5, 15 )
    oled.text( valuez, 5, 25 )
    oled.show()
    print("X: ", x, "g, Y: ", y, "g, Z: ", z, "g")
    time.sleep(1)