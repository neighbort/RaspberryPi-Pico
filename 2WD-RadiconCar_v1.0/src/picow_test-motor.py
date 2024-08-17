from machine import Pin
import time 

lf = 16		# 左モータ正転（前進）
lb = 17		# 左モータ反転（後進）
rf = 20		# 右モータ正転（前進）
rb = 21		# 右モータ反転（後進）

left_forw = Pin( lf, Pin.OUT )
left_back = Pin( lb, Pin.OUT )
right_forw = Pin( rf, Pin.OUT )
right_back = Pin( rb, Pin.OUT )

left_forw.low()
left_back.low()
right_forw.low()
right_back.low()

# Test Start
right_forw.high()
time.sleep( 1 )
right_forw.low()
time.sleep( 1 )

right_back.high()
time.sleep( 1 )
right_back.low()
time.sleep( 1 )

left_forw.high()
time.sleep( 1 )
lefy_forw.low()
time.sleep( 1 )

left_back.high()
time.sleep( 1 )
left_back.low()
time.sleep( 1 )