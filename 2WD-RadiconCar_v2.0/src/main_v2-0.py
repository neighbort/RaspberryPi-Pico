import network
import socket
import time
import ujson
from machine import Pin, I2C, PWM

# Set up MMA8452
i2c_mma8452 = I2C( 0, scl=Pin(1), sda=Pin(0) )
print(hex(i2c_mma8452.scan()[0]))
MMA8452_ADDR = 0x1c
REG_WHO_AM_I = 0x0D
REG_CTRL_REG1 = 0x2A
REG_XYZ_DATA_CFG = 0x0E
REG_CTRL_REG2 = 0x2B
REG_OUT_X_MSB = 0x01
i2c_mma8452.writeto_mem(MMA8452_ADDR, REG_CTRL_REG1, b'\x01')

# Set up Low Pass Filter
alpha = 0.8  # フィルタ係数, 0~1.0
x_filtered, y_filtered, z_filtered = 0, 0, 0

# モータ制御用のクラス
class motor_ctl_2wd():
    def __init__(self, lf, lb, rf, rb, freq, speed=40000):
        """
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
        """
        # モータードライバのピン設定
        self.left_forward = Pin( lf, Pin.OUT )
        self.left_backward = Pin( lb, Pin.OUT )
        self.right_forward = Pin( rf, Pin.OUT )
        self.right_backward = Pin( rb, Pin.OUT )
        # ピンの初期設定
        self.left_forward.low()
        self.left_backward.low()
        self.right_forward.low()
        self.right_backward.low()
    
    # 左右のモータを停止する関数
    def ctl_stop(self):
        self.left_forward.low()
        self.left_backward.low()
        self.right_forward.low()
        self.right_backward.low()
#        self.left_forward.duty_u16(0)
#        self.left_backward.duty_u16(0)
#        self.right_forward.duty_u16(0)
#        self.right_backward.duty_u16(0)
    
    # 左右のモータを正転し前進する関数
    def ctl_forward(self):
        self.left_forward.high()
        self.left_backward.low()
        self.right_forward.high()
        self.right_backward.low()
#        self.left_forward.duty_u16(self.speed)
#        self.left_backward.duty_u16(0)
#        self.right_forward.duty_u16(self.speed)
#        self.right_backward.duty_u16(0)
    
    # 左右のモータを反転し後進する関数
    def ctl_backward(self):
        self.left_forward.low()
        self.left_backward.high()
        self.right_forward.low()
        self.right_backward.high()
#        self.left_forward.duty_u16(0)
#        self.left_backward.duty_u16(self.speed)
#        self.right_forward.duty_u16(0)
#        self.right_backward.duty_u16(self.speed)
    
    # 右のモータを正転、左のモータを反転し反時計回りに回転する関数
    def ctl_left(self):
        self.left_forward.low()
        self.left_backward.high()
        self.right_forward.high()
        self.right_backward.low()
#        self.left_forward.duty_u16(0)
#        self.left_backward.duty_u16(self.speed)
#        self.right_forward.duty_u16(self.speed)
#        self.right_backward.duty_u16(0)
    
    # 左のモータを正転、右のモータを反転し時計回りに回転する関数
    def ctl_right(self):
        self.left_forward.high()
        self.left_backward.low()
        self.right_forward.low()
        self.right_backward.high()
#        self.left_forward.duty_u16(self.speed)
#        self.left_backward.duty_u16(0)
#        self.right_forward.duty_u16(0)
#        self.right_backward.duty_u16(self.speed)
    
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

# Wi-Fi接続の設定
ssid = 'YOUR_SSID'
password = 'YOUR_PASSWORD'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Wi-Fi接続完了待機
while not wlan.isconnected():
    time.sleep(1)

print('Connected to WiFi')
print(wlan.ifconfig())

# Webサーバーの設定
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print('Web server is running on http://{}'.format(wlan.ifconfig()[0]))

# HTMLページのテンプレート
html = """\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html>
<head>
    <title>Raspberry Pi Pico Accelerometer</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        #indicator { width: 10px; height: 10px; background-color: red; position: absolute; }
    </style>
</head>
<body>
    <h1>Accelerometer Data</h1>
    
    <h2>Control by Button </h2>
    <button onmouseover="controlCAR('forward')" onmouseout="controlCAR('stop')"
            ontouchstart="controlCAR('forward')" ontouchend="controlCAR('stop')"> FORW </button>
    <button onmouseover="controlCAR('left')" onmouseout="controlCAR('stop')"
            ontouchstart="controlCAR('left')" ontouchend="controlCAR('stop')"> LEFT </button>
    <button onmouseover="controlCAR('right')" onmouseout="controlCAR('stop')"
            ontouchstart="controlCAR('right')" ontouchend="controlCAR('stop')"> RIGHT </button>
    <button onmouseover="controlCAR('back')" onmouseout="controlCAR('stop')"
            ontouchstart="controlCAR('back')" ontouchend="controlCAR('stop')"> BACK </button>

    <canvas id="accelChart" width="400" height="200"></canvas>
    
    <!-- リアルタイムの加速度値を表示するための要素 -->
    <div id="accelValues">
        <p>X: <span id="xValue">0</span></p>
        <p>Y: <span id="yValue">0</span></p>
        <p>Z: <span id="zValue">0</span></p>
    </div>
    
    <script>
        function controlCAR(action) {
            fetch(`/${action}`, {
                method: 'POST'
            })
            .then(response => response.text())
            .then(data => console.log(data))
            .catch(error => console.error('Error:', error));
        }
    
        document.addEventListener("DOMContentLoaded", function() {
        
            var ctx = document.getElementById('accelChart').getContext('2d');
            var chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'X',
                            borderColor: 'red',
                            data: [],
                            fill: false
                        },
                        {
                            label: 'Y',
                            borderColor: 'green',
                            data: [],
                            fill: false
                        },
                        {
                            label: 'Z',
                            borderColor: 'blue',
                            data: [],
                            fill: false
                        }
                    ]
                },
                options: {
                    animation: false,
                    scales: {
                        x: {
                            display: true,
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Acceleration'
                            }
                        }
                    }
                }
            });

            function fetchData() {
                fetch('/data')
                    .then(response => response.json())
                    .then(data => {
                        var now = new Date();
                        chart.data.labels.push(now.getSeconds());
                        chart.data.datasets[0].data.push(data.x);
                        chart.data.datasets[1].data.push(data.y);
                        chart.data.datasets[2].data.push(data.z);

                        if (chart.data.labels.length > 50) {
                            chart.data.labels.shift();
                            chart.data.datasets[0].data.shift();
                            chart.data.datasets[1].data.shift();
                            chart.data.datasets[2].data.shift();
                        }

                        chart.update();

                        // 数値表示の更新
                        document.getElementById('xValue').textContent = data.x;
                        document.getElementById('yValue').textContent = data.y;
                        document.getElementById('zValue').textContent = data.z;
                    })
                    .catch(error => {
                        console.error('Error fetching data:', error);
                    });
            }

            setInterval(fetchData, 1000);
        });
    </script>
</body>
</html>
"""

mctl = motor_ctl_2wd(16, 17, 20, 21, 500)
# Webサーバーループ
while True:
    cl, addr = s.accept()
    print('Client connected from', addr)
    request = b""
    try:
        while True:
            part = cl.recv(1024)
            request += part
            if len(part) < 1024:
                break
        request_str = request.decode()
#        print('Request:', request_str)
        if 'GET /data' in request_str:
            x, y, z = read_acceleration(i2c_mma8452, MMA8452_ADDR, REG_OUT_X_MSB)
            data = {'x': x, 'y': y, 'z': z}
            response = 'HTTP/1.1 200 OK\nContent-Type: application/json\n\n'
            response += ujson.dumps(data)
#            print('Data sent:', data)  # デバッグ用に追加
            cl.send(response)
        elif '/stop' in request:
            mctl.ctl_stop()
            print("input stop command")
        elif '/forward' in request:
            mctl.ctl_forward()
            print("input frwd command")
        elif '/left' in request:
            mctl.ctl_left()
            print("input left command")
        elif '/right' in request:
            mctl.ctl_right()
            print("input right command")
        elif '/back' in request:
            mctl.ctl_backward()
            print("input back command")
        elif '/control' in request:
            try:
                params = request.split(' ')[1]  # パス部分を取得
                query = params.split('/control?')[1]
                x_pos = int(float(query.split('&')[0].split('=')[1]))
                y_pos = int(float(query.split('&')[1].split('=')[1]))
                print(x_pos, y_pos)
                ux, uy, th_rad = conv_position2unitcircle(x_pos, y_pos, 400, 400)
                left, right, left_duty, right_duty = conv_unitcircle2duty(ux, uy, th_rad)
                mctl.ctl_universal(left, right, left_duty, right_duty)
            except (IndexError, ValueError):
                print("Invalid control parameters")
        else:
            cl.send(html)
    except Exception as e:
        print('Error:', e)
    finally:
        cl.close()