from machine import Pin
from UpyIrRx import UpyIrRx
from UpyIrTx import UpyIrTx
import json
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


## function o define HTML
def generate_html(ir_signals):
    html = "<html><body><h1>IR Remote Controller</h1>"
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