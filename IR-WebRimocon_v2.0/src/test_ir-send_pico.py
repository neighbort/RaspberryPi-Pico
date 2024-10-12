from machine import Pin
from UpyIrRx import UpyIrRx
from UpyIrTx import UpyIrTx
import json
import os

print("hello")

rx_pin = Pin(14, Pin.IN)
rx = UpyIrRx(rx_pin)

tx_pin = Pin(28, Pin.OUT)
tx = UpyIrTx(0, tx_pin)

if "command" in os.listdir():
    with open("command", 'r') as f:
            cmdlist = json.load(f)
            print(cmdlist)
else:
    cmdlist = {}
    print("command list newly created!")
    
## SEND IR CODE ##
cmdname = "test0"
tx.send(cmdlist[cmdname])
