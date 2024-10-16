from machine import Pin, I2C
import utime
from ssd1306 import SSD1306_I2C


# GPIOピンの設定
LED_PIN = 25      # LEDのピン
led = Pin(LED_PIN, Pin.OUT)
BUTTON_PIN = 16   # ボタンのピン
button = Pin( BUTTON_PIN, Pin.IN, Pin.PULL_DOWN )
SW_W_PIN = 17
sw_w = Pin( SW_W_PIN, Pin.IN, Pin.PULL_DOWN )
SW_B_PIN = 18
sw_b = Pin( SW_B_PIN, Pin.IN, Pin.PULL_DOWN )


# モールス信号のマッピング
morse_code_map = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D',
    '.': 'E', '..-.': 'F', '--.': 'G', '....': 'H',
    '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
    '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P',
    '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
    '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
    '-.--': 'Y', '--..': 'Z',
    '-----': '0', '.----': '1', '..---': '2', '...--': '3',
    '....-': '4', '.....': '5', '-....': '6', '--...': '7',
    '---..': '8', '----.': '9',
}


# Set up Display
WIDTH  = 128
HEIGHT = 64
i2c = I2C( 0 )
i2c.scan()


# Init display
oled = SSD1306_I2C( WIDTH, HEIGHT, i2c )
oled.fill( 0 )
oled.text( "Press button?", 5, 5 )
oled.text( "to input Morse", 5, 15 )
oled.show()


def translate_morse(signal):
    return morse_code_map.get(signal, '?')


def loop_morse(button, led, sw_w, sw_b, translated_char):
    signal = ""
    start_time = 0
    last_press_time = 0
    initial_display_done = False
    
    while True:
        if button.value() == 1:  # ボタンが押されるとLOW
            led.on()  # ボタンを押している間LEDを点灯
            if start_time == 0:
                start_time = utime.ticks_ms()
                # ボタンが初めて押された時の初期表示をクリア
                if not initial_display_done:
                    oled.init_display()
                    initial_display_done = True
            last_press_time = utime.ticks_ms()
        else:
            led.off()  # ボタンが離されたらLEDを消灯
            if start_time > 0:
                duration = utime.ticks_diff(utime.ticks_ms(), start_time)
                if duration >= 300:  # 0.3秒以上なら「－」
                    signal += "-"
                else:  # それ以下なら「・」
                    signal += "."
                
                # リアルタイムでLCDの2段目に表示
                oled.init_display()
                oled.text( signal, 5, 5 )
                oled.text( translated_char, 5, 15)
                oled.show()
                
                start_time = 0

        # 信号の確定条件：ボタンが押されていない状態が0.5秒以上続く
        if sw_w.value() == 1:
            translated_char += translate_morse(signal)
            signal_disp = signal
            signal = ""
            
            oled.init_display()
            oled.text( signal, 5, 5 )
            oled.text( translated_char, 5, 15)
            oled.show()
        
        # 入力終了
        if sw_b.value() == 1:
            oled.init_display()
            oled.text( "Press button?", 5, 5 )
            oled.text( "to input Morse", 5, 15 )
            oled.show()
            translated_char = ""
            signal = ""
        
        utime.sleep(0.1)

if __name__ == "__main__":
    while True:
        try:
            translated_char = ""
            loop_morse(button, led, sw_w, sw_b, translated_char)
        except KeyboardInterrupt:
            break
