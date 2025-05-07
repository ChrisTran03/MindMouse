import RPi.GPIO as GPIO
import os
import time
import subprocess

BUTTON_GPIO = 3  # GPIO3 = Pin 5

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

time.sleep(5)

def shutdown_gui_and_system():
    print("Button pressed! Shutting down...")

    # Step 1: Close your GUI (e.g., typescroller)
    subprocess.call(["pkill", "-f", "typescroller64.py"])
    time.sleep(2)

    # Step 2: Shut down system
    subprocess.call(["sudo", "shutdown", "-h", "now"])

try:
    while True:
        if GPIO.input(BUTTON_GPIO) == GPIO.LOW:
            time.sleep(0.1)
            if GPIO.input(BUTTON_GPIO) == GPIO.LOW:
                shutdown_gui_and_system()
                time.sleep(2)  # debounce to prevent retrigger
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
