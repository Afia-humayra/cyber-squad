import pigpio
from time import sleep

servo_pin = 12
pi = pigpio.pi()

if not pi.connected:
    exit()

try:
    while True:
        pi.set_servo_pulsewidth(servo_pin, 500)   # 0°
        sleep(1)
        pi.set_servo_pulsewidth(servo_pin, 1500)  # 90°
        sleep(1)
        pi.set_servo_pulsewidth(servo_pin, 500)   # 0°
        sleep(1)
except KeyboardInterrupt:
    pi.set_servo_pulsewidth(servo_pin, 0)  # turn off
    pi.stop()

