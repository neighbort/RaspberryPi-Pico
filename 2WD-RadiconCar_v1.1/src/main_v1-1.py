import network
import socket
from machine import Pin, PWM
import time
import math

# Wi-Fi接続情報
SSID = 'your_SSID'
PASSWORD = 'your_PASSWORD'

def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        print('Connecting to WiFi...')
        time.sleep(1)

    print('Connected to WiFi')
    print(wlan.ifconfig())

connect_to_wifi()

# モータ制御用のクラス
class motor_ctl_2wd():
    def __init__(self, lf, lb, rf, rb, freq, speed=40000):
        # モータードライバのピン設定
        self.left_forward = PWM(Pin(lf))
        self.left_backward = PWM(Pin(lb))
        self.right_forward = PWM(Pin(rf))
        self.right_backward = PWM(Pin(rb))
        # PWM制御の周波数設定
        self.left_forward.freq(freq)
        self.left_backward.freq(freq)
        self.right_forward.freq(freq)
        self.right_backward.freq(freq)
        # ピンの初期設定
        self.left_forward.duty_u16(0)
        self.left_backward.duty_u16(0)
        self.right_forward.duty_u16(0)
        self.right_backward.duty_u16(0)
        # PWM初期速度設定
        self.speed = int(speed)
    
    # 左右のモータを停止する関数
    def ctl_stop(self):
        self.left_forward.duty_u16(0)
        self.left_backward.duty_u16(0)
        self.right_forward.duty_u16(0)
        self.right_backward.duty_u16(0)
    
    # 左右のモータを正転し前進する関数
    def ctl_forward(self):
        self.left_forward.duty_u16(self.speed)
        self.left_backward.duty_u16(0)
        self.right_forward.duty_u16(self.speed)
        self.right_backward.duty_u16(0)
    
    # 左右のモータを反転し後進する関数
    def ctl_backward(self):
        self.left_forward.duty_u16(0)
        self.left_backward.duty_u16(self.speed)
        self.right_forward.duty_u16(0)
        self.right_backward.duty_u16(self.speed)
    
    # 右のモータを正転、左のモータを反転し反時計回りに回転する関数
    def ctl_left(self):
        self.left_forward.duty_u16(0)
        self.left_backward.duty_u16(self.speed)
        self.right_forward.duty_u16(self.speed)
        self.right_backward.duty_u16(0)
    
    # 左のモータを正転、右のモータを反転し時計回りに回転する関数
    def ctl_right(self):
        self.left_forward.duty_u16(self.speed)
        self.left_backward.duty_u16(0)
        self.right_forward.duty_u16(0)
        self.right_backward.duty_u16(self.speed)
    
    # 左右のモータの正転反転とduty比を入力して制御する関数
    def ctl_universal(self, left, right, left_duty=1.0, right_duty=1.0, minspeed=30000, maxspeed=60000):
        if left_duty < 0.0:
            left_duty = left_duty * (-1)
        if right_duty < 0.0:
            right_duty = right_duty * (-1)
        if 1.0 < right_duty:
            right_duty = 1.0
        if 1.0 < left_duty:
            left_duty = 1.0
            
        if left == 1:
            self.left_forward.duty_u16(int(minspeed + (maxspeed-minspeed)*left_duty))
            self.left_backward.duty_u16(0)
        elif left == -1:
            self.left_forward.duty_u16(0)
            self.left_backward.duty_u16(int(minspeed + (maxspeed-minspeed)*left_duty))
        else:
            self.left_forward.duty_u16(0)
            self.left_backward.duty_u16(0)
        
        if right == 1:
            self.right_forward.duty_u16(int(minspeed + (maxspeed-minspeed)*left_duty))
            self.right_backward.duty_u16(0)
        elif right == -1:
            self.right_forward.duty_u16(0)
            self.right_backward.duty_u16(int(minspeed + (maxspeed-minspeed)*left_duty))
        else:
            self.right_forward.duty_u16(0)
            self.right_backward.duty_u16(0)
            
    def set_speed(self, speed):
        if speed < 0:
            speed = 0
        if 65535 < speed:
            speed = 65535
        self.speed = int(speed)

# 枠内のX, Y座標を半径1の単位円内の位置ux, uyと角度th_radに変換する関数
def conv_position2unitcircle(x, y, width_x, width_y):
    center_x = width_x / 2
    center_y = width_y / 2
    radius = min(center_x, center_y)
    rtx = (x-center_x)
    rty = (-1) * (y-center_y)
    th_rad = math.atan2(rty, rtx)
    rtd = math.sqrt(rtx**2 + rty**2)
    ur = min(1.0, rtd/radius)
    ux = ur * math.cos(th_rad)
    uy = ur * math.sin(th_rad)
    return ux, uy, th_rad
    
# 半径1の単位円内の位置ux, uyと角度th_radから、左右の車輪のduty比に変換する関数
def conv_unitcircle2duty(ux, uy, th_rad):
    rad = min(math.sqrt(ux**2 + uy**2), 1.0)
    if math.radians(-10)<=th_rad and th_rad <= math.radians(10):
        return 1, -1, rad, rad
    elif math.radians(170)<=th_rad or th_rad <= math.radians(-170):
        return -1, 1, rad, rad
    elif math.radians(10)<=th_rad and th_rad <= math.radians(170):
        if 0 <= ux:
            return 1, 1, rad, rad*abs(uy)
        elif ux < 0:
            return 1, 1, rad*abs(uy), rad
    elif th_rad<math.radians(-10) and math.radians(-170)<th_rad:
        if 0 <= ux:
            return -1, -1, rad, rad*abs(uy)
        elif ux < 0:
            return -1, -1, rad, rad*abs(uy)


def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)
    
    # モータードライバのピン設定
    ## 16 : 左モータの正転（前進）
    ## 17 : 左モータの反転（後進）
    ## 20 : 右モータの正転（前進）
    ## 21 : 右モータの反転（後進）
    mctl = motor_ctl_2wd(16, 17, 20, 21, 400)

    try:
        while True:
            cl, addr = s.accept()
            print('Client connected from', addr)
            request = cl.recv(1024)
            request = str(request)

            # マウス/タッチ位置に基づいたモーター制御
            if '/control' in request:
                try:
                    params = request.split(' ')[1]  # パス部分を取得
                    query = params.split('/control?')[1]
                    x_pos = int(float(query.split('&')[0].split('=')[1]))
                    y_pos = int(float(query.split('&')[1].split('=')[1]))
                    ux, uy, th_rad = conv_position2unitcircle(x_pos, y_pos, 400, 400)
                    left, right, left_duty, right_duty = conv_unitcircle2duty(ux, uy, th_rad)
                    mctl.ctl_universal(left, right, left_duty, right_duty)
                except (IndexError, ValueError):
                    print("Invalid control parameters")
            elif '/stop' in request:
                mctl.ctl_stop()
            elif '/forward' in request:
                mctl.ctl_forward()
            elif '/left' in request:
                mctl.ctl_left()
            elif '/right' in request:
                mctl.ctl_right()
            elif '/back' in request:
                mctl.ctl_backward()
        
            response = html_page()
            cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
            cl.send(response)
            cl.close()
    except (KeyboardInterrupt):
        s.close()
    finally:
        s.close()

# WEBサーバに接続した際に表示されるhtml
def html_page():
    html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Raspberry Pi Pico Car</title>
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
            <style>
                #control-area {
                    width: 400px;
                    height: 400px;
                    border: 2px solid black;
                    position: relative;
                }
            </style>
        </head>
        <body>
            <h1>Raspberry Pi Pico Car Control</h1>
            <h2>Control by Button </h2>
            
            <button onmouseover="controlCAR('forward')" onmouseout="controlCAR('stop')"
                    ontouchstart="controlCAR('forward')" ontouchend="controlCAR('stop')"> FORW </button>
            <button onmouseover="controlCAR('left')" onmouseout="controlCAR('stop')"
                    ontouchstart="controlCAR('left')" ontouchend="controlCAR('stop')"> LEFT </button>
            <button onmouseover="controlCAR('right')" onmouseout="controlCAR('stop')"
                    ontouchstart="controlCAR('right')" ontouchend="controlCAR('stop')"> RIGHT </button>
            <button onmouseover="controlCAR('back')" onmouseout="controlCAR('stop')"
                            ontouchstart="controlCAR('back')" ontouchend="controlCAR('stop')"> BACK </button>
            
            <h2>Control by Mouse/Touch Position </h2>
            <div id="control-area"></div>
            
            <script>
                function controlCAR(action) {
                    fetch(`/${action}`, {
                        method: 'POST'
                    })
                    .then(response => response.text())
                    .then(data => console.log(data))
                    .catch(error => console.error('Error:', error));
                }
            
                const controlArea = document.getElementById('control-area');

                controlArea.addEventListener('mousemove', function(event) {
                    const rect = controlArea.getBoundingClientRect();
                    const x = event.clientX - rect.left;
                    const y = event.clientY - rect.top;
                    controlCar(x, y);
                });

                controlArea.addEventListener('touchmove', function(event) {
                    const rect = controlArea.getBoundingClientRect();
                    const x = event.touches[0].clientX - rect.left;
                    const y = event.touches[0].clientY - rect.top;
                    controlCar(x, y);
                    event.preventDefault(); // prevent scrolling
                });

                controlArea.addEventListener('mouseleave', function() {
                    stopCar();
                });
                controlArea.addEventListener('mouseleave', function(event) {
                    stopCar();
                });

                controlArea.addEventListener('touchend', function() {
                    stopCar();
                });

                function controlCar(x, y) {
                    setInterval(fetch(`/control?x=${x}&y=${y}`), 100);
                }

                function stopCar() {
                    fetch('/stop');
                }
            </script>
        </body>
        </html>
    """
    return html

start_server()