import pigpio
import tkinter as tk
from time import sleep
from threading import Thread

# Servo setup
servo_pin = 12
pi = pigpio.pi()

if not pi.connected:
    print("❌ Failed to connect to pigpio daemon. Run: sudo pigpiod")
    exit()

# Servo loop function (runs in background thread)
def run_servo():
    try:
        while True:
            pi.set_servo_pulsewidth(servo_pin, 500)   # 0°
            sleep(1)
            pi.set_servo_pulsewidth(servo_pin, 1500)  # 90°
            sleep(1)
            pi.set_servo_pulsewidth(servo_pin, 500)   # 0°
            sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        pi.set_servo_pulsewidth(servo_pin, 0)
        pi.stop()

# GUI setup
root = tk.Tk()
root.title("Servo Control")
root.attributes("-fullscreen", True)  # Fullscreen
root.configure(bg="black")

label = tk.Label(
    root,
    text="Servo running in loop...\nPress ESC to exit",
    font=("Arial", 32),
    fg="white",
    bg="black"
)
label.pack(expand=True)

# Exit on ESC key
root.bind("<Escape>", lambda e: root.destroy())

# Start servo thread
servo_thread = Thread(target=run_servo, daemon=True)
servo_thread.start()

# Start GUI loop
root.mainloop()

# Cleanup when window closed
pi.set_servo_pulsewidth(servo_pin, 0)
pi.stop()

