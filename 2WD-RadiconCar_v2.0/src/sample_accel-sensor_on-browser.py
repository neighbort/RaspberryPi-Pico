import network
import socket
import time
import ujson
from machine import Pin, I2C

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
ssid = 'Buffalo-G-13D0'
password = '5gjswfifgyhr6'

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
</head>
<body>
    <h1>Accelerometer Data</h1>
    <canvas id="accelChart" width="400" height="200"></canvas>
    
    <!-- リアルタイムの加速度値を表示するための要素 -->
    <div id="accelValues">
        <p>X: <span id="xValue">0</span></p>
        <p>Y: <span id="yValue">0</span></p>
        <p>Z: <span id="zValue">0</span></p>
    </div>

    <script>
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

            setInterval(fetchData, 100);
        });
    </script>
</body>
</html>
"""

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
        print('Request:', request_str)
        if 'GET /data' in request_str:
            x, y, z = read_acceleration(i2c_mma8452, MMA8452_ADDR, REG_OUT_X_MSB)
            data = {'x': x, 'y': y, 'z': z}
            response = 'HTTP/1.1 200 OK\nContent-Type: application/json\n\n'
            response += ujson.dumps(data)
            print('Data sent:', data)  # デバッグ用に追加
            cl.send(response)
        else:
            cl.send(html)
    except Exception as e:
        print('Error:', e)
    finally:
        cl.close()