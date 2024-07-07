from machine import Pin, I2C, deepsleep
import time
from ssd1306 import SSD1306_I2C

# Define conversion from second to minutes
def sec2min4disp(count_sec):
    min_min = count_sec // 60
    min_sec = count_sec % 60
    disp = str(min_min) + "min" + str(min_sec) + "sec"
    return disp

# Init setup: turn off wifi tip to save power consumption
Pin(23, Pin.OUT).low()

# Set up Botton
SW_R_PIN = 16
sw_r = Pin( SW_R_PIN, Pin.IN, Pin.PULL_DOWN )
SW_W_PIN = 17
sw_w = Pin( SW_W_PIN, Pin.IN, Pin.PULL_DOWN )
SW_B_PIN = 18
sw_b = Pin( SW_B_PIN, Pin.IN, Pin.PULL_DOWN )

# Set up Display
WIDTH  = 128
HEIGHT = 64
i2c = I2C( 0 )
i2c.scan()

# Set up LED
ledpin = 25
led = Pin( ledpin, Pin.OUT )
led.value(0)

# Variable
default = 30
count_sec = default
stdslp = 0.2

# Init display
oled = SSD1306_I2C( WIDTH, HEIGHT, i2c )
oled.fill( 0 )
oled.text( "How long?", 5, 5 )
oled.text( sec2min4disp(count_sec), 5, 15 )
oled.show()

# Main Roop
while True:
    # Setting Mode
    if( sw_r.value() == 1 ):
        count_sec -= 10
        count_sec = max(10, count_sec)
        oled.init_display()
        oled.text( "How long?", 5, 5 )
        oled.text( sec2min4disp(count_sec), 5, 15 )
        oled.show()
    if( sw_b.value() == 1 ):
        count_sec += 10
        oled.init_display()
        oled.text( "How long?", 5, 5 )
        oled.text( sec2min4disp(count_sec), 5, 15 )
        oled.show()

    # Setting flag for LED
    flag = True
    
    # Counting Mode
    if( sw_w.value() == 1 ):
        # Turn on LED
        led.value(1)
        
        # Count Roop
        while count_sec > 0:
            # Reduce count every 1 sec
            time.sleep(1.0)
            count_sec -= 1
            
            # Display remainning count every 1 sec
            oled.init_display()
            oled.text( "Count", 5, 5 )
            oled.text( sec2min4disp(count_sec), 5, 15 )
            oled.show()
            
            # Hold counting
            if sw_r.value() == 1:
                oled.init_display()
                oled.text( "Hold", 5, 5 )
                oled.text( sec2min4disp(count_sec), 5, 15 )
                oled.show()
                time.sleep(stdslp)
                while sw_b.value() == 0:
                    time.sleep(stdslp)
            
            # Break out from counting
            if sw_r.value() == 1 and sw_b.value() == 1:
                count_sec = default
                break
            
        # Finish Roop: last until White Button is pushed
        oled.init_display()
        oled.text( "Fibish !!", 5, 5 )
        oled.text( sec2min4disp(count_sec), 5, 15 )
        oled.show()
        while sw_w.value() == 0:
            # for LED
            flag = not flag
            led.value(flag)
            time.sleep(stdslp)
        # Turn off LED
        led.value(0)
        time.sleep(2)
        count_sec = default
        oled.init_display()
        oled.text( "How long?", 5, 5 )
        oled.text( sec2min4disp(count_sec), 5, 15 )
        oled.show()
        
    time.sleep( stdslp )
    