import speech_recognition as sr
import pygame
import io
import time
import random
import subprocess
import webbrowser
import os
import sys
import logging
import re
import threading
import tkinter as tk
from google.cloud import vision
import pigpio

# ==================================================
# BASIC SETUP
# ==================================================
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'keytoken.json'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
pygame.mixer.init()

# ==================================================
# SERVO SETUP USING pigpio
# ==================================================
SERVO_PIN = 12
pi = pigpio.pi()
if not pi.connected:
    print("❌ Failed to connect to pigpio daemon. Run: sudo pigpiod")
    sys.exit(1)

def move_servo_to(angle):
    """Move servo to a specific angle."""
    pulse = 500 + (angle / 180.0) * 2000
    pi.set_servo_pulsewidth(SERVO_PIN, pulse)
    logger.info(f"Servo moved to {angle}°")
    time.sleep(0.5)

def servo_feeding_action():
    """Run feeding servo action in a thread."""
    def feed():
        logger.info("Servo feeding action start")
        move_servo_to(90)
        time.sleep(2)
        move_servo_to(0)
        logger.info("Servo feeding action complete")
    threading.Thread(target=feed, daemon=True).start()

def cleanup_servo():
    pi.set_servo_pulsewidth(SERVO_PIN, 0)
    pi.stop()
    logger.info("Servo stopped and pigpio cleaned up")def cleanup_servo():
    global pi
    try:
        if pi is not None:
            if hasattr(pi, "connected") and pi.connected:
                try:
                    pi.set_servo_pulsewidth(SERVO_PIN, 0)
                except Exception as e:
                    logger.warning(f"Servo already inactive or disconnected: {e}")
                try:
                    pi.stop()
                except Exception as e:
                    logger.warning(f"pigpio stop failed: {e}")
                logger.info("Servo stopped and pigpio cleaned up")
            else:
                logger.info("pigpio not connected � skipping cleanup")
        else:
            logger.info("pi object is None � nothing to clean up")
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")


# ==================================================
# TKINTER FULLSCREEN DISPLAY
# ==================================================
root = tk.Tk()
root.attributes("-fullscreen", True)
root.configure(bg="black")
root.bind("<Escape>", lambda e: (cleanup_servo(), root.destroy()))

status_label = tk.Label(
    root, text="Initializing Homi...", font=("Arial", 32),
    fg="white", bg="black"
)
status_label.pack(expand=True)

def update_status(msg):
    """Update fullscreen display text."""
    def _update():
        status_label.config(text=msg)
    root.after(0, _update)
    logger.info(f"Status: {msg}")

# ==================================================
# AUDIO + SPEECH + OCR FUNCTIONS
# ==================================================
AUDIO_FILES = {
    "ocr_processing": "audio_files/ocr_processing.mp3",
    "taking_photo": "audio_files/taking_photo.mp3",
    "topic_found": "audio_files/topic_found.wav",
    "topic_not_found": "audio_files/topic_not_found.mp3",
    "ready": "audio_files/ready.wav",
    "error": "audio_files/error.mp3",
    "feeding": "audio_files/feeding.wav"
}

def play_audio(path):
    try:
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        else:
            logger.warning(f"Missing audio: {path}")
    except Exception as e:
        logger.error(f"Audio error: {e}")

def capture_image():
    update_status("📷 Capturing image...")
    play_audio(AUDIO_FILES["taking_photo"])
    try:
        subprocess.run([
            "rpicam-still", "-o", "captured.jpg",
            "-t", "2000", "--width", "1920", "--height", "1080"
        ], check=True)
        return "captured.jpg"
    except Exception as e:
        logger.error(e)
        play_audio(AUDIO_FILES["error"])
        return None

def perform_ocr(image_path):
    update_status("🔍 Performing OCR...")
    play_audio(AUDIO_FILES["ocr_processing"])
    try:
        client = vision.ImageAnnotatorClient()
        with io.open(image_path, 'rb') as f:
            content = f.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        if response.text_annotations:
            text = response.text_annotations[0].description.lower()
            logger.info(f"OCR Text: {text[:80]}")
            return text
    except Exception as e:
        logger.error(e)
    return None

# ==================================================
# SPEECH + CALLBACK
# ==================================================
def setup_mic():
    mic = sr.Microphone()
    logger.info("Microphone ready.")
    return mic

def callback(recognizer, audio):
    try:
        text = recognizer.recognize_google(audio).lower()
        logger.info(f"Heard: {text}")
        update_status(f"🎤 Heard: {text}")

        if "feed" in text or "hungry" in text:
            play_audio(AUDIO_FILES["feeding"])
            servo_feeding_action()
            update_status("🍽 Feeding in progress...")
            return

        if "homework" in text or "solve" in text:
            update_status("📄 Starting OCR...")
            img = capture_image()
            if not img: return
            text_data = perform_ocr(img)
            if text_data:
                play_audio(AUDIO_FILES["topic_found"])
                update_status("✅ Topic identified.")
            else:
                play_audio(AUDIO_FILES["topic_not_found"])
                update_status("❌ Topic not found.")
            return

        update_status("🤔 Unrecognized command.")
    except Exception as e:
        logger.error(e)
        play_audio(AUDIO_FILES["error"])

# ==================================================
# MAIN FUNCTION
# ==================================================
def main():
    update_status("🎙 Calibrating microphone...")
    recognizer = sr.Recognizer()
    mic = setup_mic()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    update_status("✅ Ready! Say a command...")
    play_audio(AUDIO_FILES["ready"])
    recognizer.listen_in_background(mic, callback)

    # Keep the GUI alive
    root.mainloop()
    cleanup_servo()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup_servo()
        root.destroy()

