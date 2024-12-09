from machine import Pin, I2C, deepsleep
import time
from ssd1306 import SSD1306_I2C

# Set up Display
WIDTH  = 128
HEIGHT = 64
i2c = I2C( 0 )
i2c.scan()

# Set up LED
ledpin = 25
led = Pin( ledpin, Pin.OUT )
led.value(0)

# Init display
oled = SSD1306_I2C( WIDTH, HEIGHT, i2c )
oled.fill( 0 )
oled.text( "Count 10sec !", 5, 5 )
oled.show()
time.sleep(3)

count = 0
led.value(1)
while True:
    oled.init_display()
    oled.text( "Hello world", 5, 5 )
    oled.text( str(count), 5, 15 )
    oled.show()
    count += 1
    time.sleep(1)
    if count == 10:
        break

oled.init_display()
oled.text( "Finish !!", 5, 5 )
oled.show()
led.value(0)

    