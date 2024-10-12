from machine import Pin, I2C
from UpyIrRx import UpyIrRx
from UpyIrTx import UpyIrTx
import json
import ujson
import os
import network
import socket
import time

## Function to connect to Wi-Fi
def connect_to_wifi(SSID, PASSWORD):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(0.5)
    print("Connected to WiFi")
    status = wlan.ifconfig()
    print('ip = ' + status[0])


## Function to read ir-command list file
def load_ir_signals(IR_FILE):
    try:
        with open(IR_FILE, 'r') as f:
            ir_signals = json.load(f)
    except OSError:
        ir_signals = {}
    return ir_signals


## Function to dump ir-command list file
def save_ir_signals(IR_FILE, ir_signals):
    with open(IR_FILE, 'w') as f:
        json.dump(ir_signals, f)


## Function to record ir-signal
def receive_ir_signal(ir_signals, cmdname, rx):
    print("Waiting for IR signal...")
    while True:
        print(".\n")
        rx.record(3000)
        if rx.get_mode() == UpyIrRx.MODE_DONE_OK:
            signal_list = rx.get_calibrate_list()
            ir_signals[cmdname] = signal_list
            break
    print(f"Received IR signal: {cmdname}")
    return ir_signals


## Function to output ir-signal
def send_ir_signal(ir_signals, cmdname, tx):
    print(f"Send a Sgnal named {cmdname}")
    tx.send(ir_signals[cmdname])
    

## Function to measure Temp and Humd by DHT20
def dht20_read(i2c, DHT20_ADDR):
    # Start up sequence
    i2c.writeto(DHT20_ADDR, b'\xAC\x33\x00')
    time.sleep(0.1)  # Delay
    # Read data
    data = i2c.readfrom(DHT20_ADDR, 6)
    # Data correction
    hum_raw = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
    temp_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
    humidity = hum_raw / 1048576 * 100  # Humidity[%]
    temperature = temp_raw / 1048576 * 200 - 50  # Temperature[°C]
    return temperature, humidity


## function o define HTML
def generate_html(ir_signals):
    html = """HTTP/1.1 200 OK
    <!DOCTYPE html>
    """
    html += "<html><head>"
    html += "<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>"
    html += "</head>"
    
    html += "<body><h1>IR Remote Controller</h1>"
    html += "<h2>IR Signal Record</h2>"
    html += "<form action='/save' method='get'>"
    html += "Signal Name: <input type='text' name='name'>"
    html += "<input type='submit' value='Record IR Signal'></form><br><br>"
    
    html += "<h2>Recorded IR Signals</h2>"
    for name in ir_signals:
        html += f"<form action='/send' method='get'>"
        html += f"<input type='hidden' name='name' value='{name}'>"
        html += f"<input type='submit' value='Send {name}'></form><br>"

    html += "<h2>Delete IR Signals</h2>"
    for name in ir_signals:
        html += f"<form action='/delete' method='get'>"
        html += f"<input type='hidden' name='name' value='{name}'>"
        html += f"<input type='submit' value='Delete {name}'></form><br>"

    html += "<div><h2>Temperature: <span id='tempData'>-- C</span></h2>"
    html += "<h2>Humidity: <span id='humidityData'>-- %</span></h2></div>"
    html += "<canvas id='tempHumidityChart' width='400' height='200'></canvas>"
    
    html += """<script>
        document.addEventListener("DOMContentLoaded", function() {
        
            var ctx = document.getElementById('tempHumidityChart').getContext('2d');
            var chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Temp [C]',
                            borderColor: 'red',
                            data: [],
                            fill: false
                        },
                        {
                            label: 'Humd [%]',
                            borderColor: 'green',
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
                                text: 'Temp [C] / Humd [%]'
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
                        chart.data.datasets[0].data.push(data.temperature);
                        chart.data.datasets[1].data.push(data.humidity);

                        if (chart.data.labels.length > 50) {
                            chart.data.labels.shift();
                            chart.data.datasets[0].data.shift();
                            chart.data.datasets[1].data.shift();
                        }

                        chart.update();

                        // 数値表示の更新
                        document.getElementById('tempData').textContent = data.temperature;
                        document.getElementById('humidityData').textContent = data.humidity;
                    })
                    .catch(error => {
                        console.error('Error fetching data:', error);
                    });
            }

            setInterval(fetchData, 2000);
        });
    </script>
    """
        
    html += "</body></html>"
    return html


##### MAIN #####
# Setup1
SSID = 'YOUR_SSID'
PASSWORD = 'YOUR_PASSWORD'
IR_FILE = "ir_signals.json"
# Setup GPIO
rx_pin = Pin(14, Pin.IN)
rx = UpyIrRx(rx_pin)
tx_pin = Pin(28, Pin.OUT)
tx = UpyIrTx(0, tx_pin)
# Setup DHT20
i2c_dht20 = I2C( 1, scl=Pin(27), sda=Pin(26) )
print(hex(i2c_dht20.scan()[0]))
DHT20_ADDR = 0x38

# Start Wi-Fi connection
connect_to_wifi(SSID, PASSWORD)

# Starting Web Server
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print('Web server running on', addr)
ir_signals = load_ir_signals(IR_FILE)

# Main Roop
try:
    while True:
        cl, addr = s.accept()
        print('Client connected from', addr)
        request = cl.recv(1024).decode('utf-8')
    
        # Record
        if 'GET /save?' in request:
            name = request.split('name=')[1].split(' ')[0]
            name = name.replace('%20', ' ')
            ir_signals = receive_ir_signal(ir_signals, name, rx)
            save_ir_signals(IR_FILE, ir_signals)
    
        # Send
        elif 'GET /send?' in request:
            name = request.split('name=')[1].split(' ')[0]
            name = name.replace('%20', ' ')
            if name in ir_signals.keys():
                send_ir_signal(ir_signals, name, tx)
        
        # Delete
        elif 'GET /delete?' in request:
            name = request.split("name=")[1].split(' ')[0]
            name = name.replace('%20', ' ')
            if name in ir_signals.keys():
                del ir_signals[name]
                save_ir_signals(IR_FILE, ir_signals)
        
        # Temp and Humd 
        elif 'GET /data' in request:
            temp, humd = dht20_read(i2c_dht20, DHT20_ADDR)
            result = {'temperature': temp, 'humidity': humd}
            res = 'HTTP/1.1 200 OK\nContent-Type: application/json\n\n'
            res += ujson.dumps(result)
            cl.send(res)
            cl.close()
            continue
            
        # Return HTML Page
        ir_signals = load_ir_signals(IR_FILE)
        response = generate_html(ir_signals)
        cl.send('HTTP/1.1 200 OK\n')
        cl.send('Content-Type: text/html\n')
        cl.send('Connection: close\n\n')
        cl.sendall(response)
        cl.close()
except:
    cl.close()
    s.close()