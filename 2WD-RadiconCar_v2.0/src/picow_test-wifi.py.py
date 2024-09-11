import network
import socket
import time
from machine import Pin

led = Pin("LED", Pin.OUT) # use on-board LED 

ssid = 'your_SSID'        # ネットワークのSSID名を記載する
password = 'your_PASSWORD'   # ネットワークのパスワードを記載する

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

wlan.connect(ssid, password)

# Pico Wにアクセスした際に表示するWebページのHTML
html = """<!DOCTYPE html>
<html>
  <head> <title>Pico W</title> </head>
  <body> <h1>Pico W</h1>
    <p>%s</p>
  </body>
</html>
"""

# 接続できるまで待機する
max_wait = 10
while max_wait > 0:
  if wlan.status() < 0 or wlan.status() >= 3:
    break
  max_wait -= 1
  print('waiting for connection...')
  time.sleep(1)

# 接続エラーのハンドリング
if wlan.status() != 3:
  raise RuntimeError('network connection failed')
else:
  print('connected')
  status = wlan.ifconfig()
  print('ip = ' + status[0])
print('if you turn led on, access to ' + status[0] + '/led/on')
print('if you turn led off, access to ' + status[0] + '/led/off')

# ソケットを開く
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)

# HTTPリクエスト, レスポンス処理
while True:
  try:
    cl, addr = s.accept()
    print('client connected from', addr)
    request = cl.recv(1024)
    print(request)

    # HTTP Request Header
    request = str(request) # ex) b'GET /led/on HTTP/1.1\r\nHost:....

    # リクエストが、LED onあるいはLED off用のパスかチェックする
    led_on = request.find('/led/on')
    led_off = request.find('/led/off')
    print('led on = ' + str (led_on))
    print('led off = ' + str (led_off))

    if led_on == 6:
      # LED on
      print('led on')
      led.value(1)
      stateis = "LED is ON"
    elif led_off == 6:
      # LED off
      print('led off')
      led.value(0)
      stateis = "LED is OFF"
    else:
      stateis = "LED is KEEPING"

    # コンテンツ作成
    response = html % stateis

    # レスポンス送信
    cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    cl.send(response)
    cl.close()

  except OSError as e:
    cl.close()
    print('connection closed')

