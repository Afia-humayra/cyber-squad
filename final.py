import tkinter as tk
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
import signal
from google.cloud import vision
import RPi.GPIO as GPIO



# Initialize pygame mixer for audio playbook
pygame.mixer.init()

# Servo configuration
SERVO_PIN = 12  # GPIO pin for servo (Physical pin 12)
servo_pwm = None

def show_fullscreen_hello():
    """Display Hello World in fullscreen with 'q' to exit - non-blocking"""
    
    def create_window():
        def exit_app(event):
            root.destroy()
        
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.configure(bg='black')
        
        # Bind 'q' key to exit
        root.bind('q', exit_app)
        root.bind('Q', exit_app)
        
        # Create label with Hello World
        label = tk.Label(
            root,
            text="Hello World",
            font=('Arial', 48, 'bold'),
            fg='white',
            bg='black'
        )
        label.pack(expand=True)
        
        root.mainloop()
    
    # Run in separate thread so it doesn't block
    thread = threading.Thread(target=create_window, daemon=True)
    thread.start()

def setup_servo():
    """Initialize servo motor at 0 degrees"""
    global servo_pwm
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        servo_pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz frequency
        servo_pwm.start(2.5)  # Start at 0 degrees (2.5% duty cycle)
        logger.info("Servo initialized at 0 degrees")
        time.sleep(1)  # Allow servo to reach position
    except Exception as e:
        logger.error(f"Servo setup error: {e}")

def move_servo_to_angle(angle):
    """Move servo to specific angle (0-180 degrees)"""
    global servo_pwm
    try:
        if servo_pwm is None:
            logger.error("Servo not initialized")
            return
            
        # Convert angle to duty cycle (2.5% = 0Â°, 12.5% = 180Â°)
        duty_cycle = 2.5 + (angle / 180.0) * 10.0
        servo_pwm.ChangeDutyCycle(duty_cycle)
        logger.info(f"Servo moved to {angle} degrees")
        time.sleep(1)  # Allow time for movement
    except Exception as e:
        logger.error(f"Servo movement error: {e}")

def servo_feeding_action():
    """Move servo to 90 degrees for 5 seconds then return to 0"""
    def feeding_thread():
        try:
            logger.info("Starting feeding action - moving servo to 90 degrees")
            move_servo_to_angle(90)
            time.sleep(5)  # Stay at 90 degrees for 5 seconds
            logger.info("Feeding action complete - returning servo to 0 degrees")
            move_servo_to_angle(0)
        except Exception as e:
            logger.error(f"Feeding action error: {e}")
    
    # Run servo action in separate thread to avoid blocking
    thread = threading.Thread(target=feeding_thread)
    thread.daemon = True
    thread.start()

def cleanup_gpio():
    """Clean up GPIO resources"""
    global servo_pwm
    try:
        if servo_pwm:
            servo_pwm.stop()
        GPIO.cleanup()
        logger.info("GPIO cleanup completed")
    except Exception as e:
        logger.error(f"GPIO cleanup error: {e}")

# Set Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'keytoken.json'

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track active subprocess for Python scripts and browser processes
active_subprocess = None
active_browser_processes = []

# Audio files for greetings
GREETING_AUDIO = [
    "audio_files/Greet1.wav",
    "audio_files/Greet2.wav"
]

# Audio files for help responses
HELP_AUDIO = [
    "audio_files/Help1.wav",
    "audio_files/Help2.wav",
    "audio_files/Help3.wav"
]

# Topic-specific audio files and file mappings
TOPIC_CONFIG = {
    "addition": {
        "file": "web-games/addition.html",
        "audio": "audio_files/addition.wav",
        "keywords": ["addition", "add", "plus", "+", "sum", "adding", "added"]
    },
    "subtraction": {
        "file": "web-games/subtraction.html", 
        "audio": "audio_files/subtraction.wav",
        "keywords": ["subtraction", "subtract", "minus", "-", "difference", "subtracting", "subtracted"]
    },
    "multiplication": {
        "file": "web-games/multiplication.html",
        "audio": "audio_files/multiplication.wav", 
        "keywords": ["multiplication", "multiply", "times", "Ã—", "*", "product", "multiplying", "multiplied"]
    },
    "division": {
        "file": "web-games/division.html",
        "audio": "audio_files/division.wav",
        "keywords": ["division", "divide", "Ã·", "/", "quotient", "dividing", "divided"]
    },
    "colours": {
        "file": "py_games/colors.py",
        "audio": "audio_files/Colors.wav",
        "keywords": ["color", "colour", "colors", "colours", "red", "blue", "green", "yellow"]
    },
    "shapes": {
        "file": "web-games/shapes.html",
        "audio": "audio_files/shapes.wav",
        "keywords": ["shape", "shapes", "circle", "square", "triangle", "rectangle", "geometry"]
    },
    "face": {
        "file": "face_parts_quiz.py", 
        "audio": "audio_files/face_detection.wav",
        "keywords": ["face", "facial", "features", "eyes", "nose", "mouth", "ears", "cheeks", "chin", "forehead", "skin", "face anatomy", "face detection", "facial recognition", "biology", "body", "human anatomy"]
    },
    "parts": {
        "file": "py_games/face_parts_quiz.py", 
        "audio": "audio_files/face_detection.wav",
        "keywords": ["face", "facial", "features", "eyes", "nose", "mouth", "ears", "cheeks", "chin", "forehead", "skin", "face anatomy", "face detection", "facial recognition", "biology", "body", "human anatomy"]
    },
    "finger": {
        "file": "py_games/finger_count.py", 
        "audio": "audio_files/finger_detection.wav",
        "keywords": ["finger", "fingers", "hand", "count", "digits", "thumb", "index", "middle", "ring", "little", "hand anatomy", "digit count", "biomechanics", "body", "biology"]
    },
    "counting": {
        "file": "py_games/finger_count.py", 
        "audio": "audio_files/finger_detection.wav",
        "keywords": ["finger", "fingers", "hand", "count", "digits", "thumb", "index", "middle", "ring", "little", "hand anatomy", "digit count", "biomechanics", "body", "biology"]
    },
    "color": {
        "file": "py_games/colors.py", 
        "audio": "audio_files/Colors.wav",
        "keywords": ["color", "colors", "hue", "spectrum", "red", "blue", "green", "yellow", "pigment", "palette", "tone", "shade", "saturation", "light", "dark"]
    },
    "colors": {
        "file": "py_games/colors.py", 
        "audio": "audio_files/Colors.wav",
        "keywords": ["color", "colors", "hue", "palette", "spectrum", "paint", "shades", "mix", "vibrancy", "primary", "secondary", "tonal", "vibrancy"]
    }
}

# Other audio files
AUDIO_FILES = {
    "no_session": "audio_files/no_session.wav",
    "ocr_processing": "audio_files/ocr_processing.mp3",
    "taking_photo": "audio_files/taking_photo.mp3",
    "topic_found": "audio_files/topic_found.wav",
    "topic_not_found": "audio_files/topic_not_found.mp3",
    "closing_game": "audio_files/closing_game.mp3",
    "thank_you": "audio_files/thank_you.mp3",
    "goodbye": "audio_files/goodbye.wav",
    "ready": "audio_files/ready.wav",
    "error": "audio_files/error.mp3",
    "camera_error": "audio_files/camera_error.wav",
    "feeding": "audio_files/feeding.wav"  # Optional: add feeding audio
}

def play_audio(file_path):
    """Play an audio file using pygame."""
    try:
        if os.path.exists(file_path):
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for the audio to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            logger.info(f"Played audio: {file_path}")
        else:
            logger.warning(f"Audio file not found: {file_path}")
            print(f"Missing audio: {os.path.basename(file_path)}")
    except Exception as e:
        logger.error(f"Error playing audio {file_path}: {e}")
        print(f"Audio error: {os.path.basename(file_path)}")

def capture_image_with_camera(output_path='captured_homework.jpg', preview_delay=5000):
    """Captures an image using Raspberry Pi camera with preview window and delay."""
    try:
        logger.info("Opening camera preview window...")
        logger.info(f"Will capture image in {preview_delay/1000} seconds...")
        
        # Use rpicam-still command with preview window
        subprocess.run([
            'rpicam-still', 
            '-o', output_path,
            '-t', str(preview_delay + 1000),  # Total time: preview + 1 sec for capture
            '--width', '1920',  # High resolution for better OCR
            '--height', '1080',
            '--preview', '0,0,640,480'  # Preview window size and position
        ], check=True)
        
        logger.info(f"Image captured successfully: {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error capturing image: {e}")
        return None
    except FileNotFoundError:
        logger.error("rpicam-still command not found. Make sure camera tools are installed.")
        return None

def detect_text_from_file(image_file):
    """Detects text from a local image file using Google Vision API."""
    try:
        client = vision.ImageAnnotatorClient()

        with io.open(image_file, 'rb') as file:
            content = file.read()

        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if response.error.message:
            logger.error(f'Google Vision API error: {response.error.message}')
            return None

        if texts:
            full_text = texts[0].description
            logger.info(f"OCR Text extracted: {full_text[:100]}...")  # Log first 100 chars
            return full_text.lower()
        else:
            logger.info("No text detected by Google Vision API")
            return None
            
    except Exception as e:
        logger.error(f"Google Vision OCR error: {e}")
        return None

def capture_and_process_image():
    """Capture image from camera and perform OCR using Google Vision API."""
    try:
        # Play audio notification
        play_audio(AUDIO_FILES.get("taking_photo", ""))
        
        # Capture image with Pi camera
        captured_image = capture_image_with_camera()
        
        if not captured_image or not os.path.exists(captured_image):
            logger.error("Failed to capture image")
            play_audio(AUDIO_FILES.get("camera_error", ""))
            return None
            
        # Play processing audio
        play_audio(AUDIO_FILES.get("ocr_processing", ""))
        
        # Perform OCR using Google Vision API
        text = detect_text_from_file(captured_image)
        
        return text
        
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        play_audio(AUDIO_FILES.get("error", ""))
        return None

def classify_topic_from_text(text):
    """Classify topic based on OCR text using keywords."""
    if not text:
        return None
        
    text_words = text.lower().split()
    
    # Check each topic's keywords
    for topic, config in TOPIC_CONFIG.items():
        for keyword in config["keywords"]:
            if keyword in text or any(keyword in word for word in text_words):
                logger.info(f"Topic '{topic}' identified from keyword: {keyword}")
                return topic
    
    # Enhanced pattern matching for math operations
    math_patterns = {
        "addition": [r'\+', r'add', r'sum', r'plus', r'\d+\s*\+\s*\d+'],
        "subtraction": [r'-', r'subtract', r'minus', r'difference', r'\d+\s*-\s*\d+'], 
        "multiplication": [r'\*', r'Ã—', r'multiply', r'times', r'product', r'\d+\s*[Ã—*]\s*\d+'],
        "division": [r'Ã·', r'/', r'divide', r'quotient', r'\d+\s*[Ã·/]\s*\d+']
    }
    
    for topic, patterns in math_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                logger.info(f"Topic '{topic}' identified from pattern: {pattern}")
                return topic
    
    logger.info("No topic identified from OCR text")
    return None

def launch_file(filename, topic):
    """Launch a Python or HTML file."""
    global active_subprocess, active_browser_processes
    if not filename:
        logger.info(f"No file specified for {topic}")
        play_audio(AUDIO_FILES.get("no_session", ""))
        return
    
    try:
        if filename.endswith(".py"):
            # Launch Python script
            python_cmd = sys.executable if sys.executable else "python3"
            active_subprocess = subprocess.Popen([python_cmd, filename])
            logger.info(f"Launched {filename} with PID {active_subprocess.pid}")
        elif filename.endswith(".html"):
            # Launch HTML file in browser
            try:
                
                process = subprocess.Popen([
                    "chromium-browser",
                    "--kiosk",                    # fullscreen kiosk mode
                    "--noerrdialogs",             # no error dialogs
                    "--disable-infobars",         # hide info bars
                    "--incognito",                # optional: private mode (no cache)
                    "--start-fullscreen",         # ensure fullscreen on startup
                    f"file://{os.path.abspath(filename)}"
                ])
                active_browser_processes.append(process)
                logger.info(f"Opened {filename} in Chromium kiosk mode with PID {process.pid}")
            except FileNotFoundError:
                try:
                    process = subprocess.Popen(["firefox", f"file://{os.path.abspath(filename)}"])
                    active_browser_processes.append(process)
                    logger.info(f"Opened {filename} in Firefox with PID {process.pid}")
                except FileNotFoundError:
                    webbrowser.open(f"file://{os.path.abspath(filename)}")
                    logger.info(f"Opened {filename} with default browser")
        else:
            logger.error(f"Unsupported file type: {filename}")
            play_audio(AUDIO_FILES.get("error", ""))
    except Exception as e:
        logger.error(f"Failed to launch {filename}: {e}")
        play_audio(AUDIO_FILES.get("error", ""))

def close_all_active_files():
    """Close all active games and browser windows."""
    global active_subprocess, active_browser_processes
    logger.info("Closing all active files!")
    play_audio(AUDIO_FILES.get("closing_game", ""))
    
    # Close Python script subprocess if running
    if active_subprocess is not None:
        try:
            active_subprocess.terminate()
            active_subprocess.wait(timeout=5)
            logger.info(f"Terminated subprocess with PID {active_subprocess.pid}")
            active_subprocess = None
        except subprocess.TimeoutExpired:
            active_subprocess.kill()
            logger.info(f"Force terminated subprocess")
            active_subprocess = None
        except Exception as e:
            logger.error(f"Error closing subprocess: {e}")
    
    # Close browser processes
    for process in active_browser_processes[:]:  # Create a copy to iterate over
        try:
            if process.poll() is None:  # Process is still running
                process.terminate()
                try:
                    process.wait(timeout=3)
                    logger.info(f"Terminated browser process with PID {process.pid}")
                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.info(f"Force killed browser process with PID {process.pid}")
            active_browser_processes.remove(process)
        except Exception as e:
            logger.error(f"Error closing browser process: {e}")
    
    # Also try to kill chromium and firefox processes by name
    try:
        subprocess.run(["pkill", "-f", "chromium"], check=False)
        subprocess.run(["pkill", "-f", "firefox"], check=False)
        logger.info("Killed chromium and firefox processes")
    except Exception as e:
        logger.error(f"Error killing browser processes: {e}")
    
    play_audio(AUDIO_FILES.get("thank_you", ""))

def close_game():
    """Legacy function - calls close_all_active_files"""
    close_all_active_files()

def setup_microphone():
    """Set up microphone with Pi-specific settings."""
    try:
        mic_list = sr.Microphone.list_microphone_names()
        logger.info(f"Available microphones: {mic_list}")
        microphone = sr.Microphone(device_index=None)
        return microphone
    except Exception as e:
        logger.error(f"Microphone setup error: {e}")
        return None

def callback(recognizer, audio):
    """Process voice commands."""
    try:
        # Convert audio to text
        text = recognizer.recognize_google(audio, language="en-US").lower()
        logger.info(f"Voice command: {text}")
        
        # Check for close/thank you commands
        close_patterns = [
            ("close" in text and "game" in text),
            ("stop" in text and "game" in text),
            ("thank" in text and "you" in text),
            ("thanks" in text),
            ("close" in text),
            ("finish" in text),
            ("done" in text),
            ("exit" in text)
        ]
        
        if any(close_patterns):
            close_all_active_files()
            return
        
        # Check for hunger/feeding command
        hunger_patterns = [
            ("i" in text and "hungry" in text),
            ("i'm" in text and "hungry" in text),
            ("hungry" in text),
            ("feed" in text and "me" in text),
            ("feeding" in text),
            ("food" in text)
        ]
        
        if any(hunger_patterns):
            logger.info("Hunger command detected - activating feeding mechanism")
            if AUDIO_FILES.get("feeding"):
                play_audio(AUDIO_FILES.get("feeding"))
            servo_feeding_action()
            return
        
        # Check for greeting commands
        if any(word in text.split() for word in ["hello", "hi", "hey"]):
            audio_file = random.choice(GREETING_AUDIO)
            logger.info(f"Playing greeting: {audio_file}")
            play_audio(audio_file)
            return
        
        # Check for help/can responses  
        if any(word in text for word in ["can", "help", "assist"]):
            audio_file = random.choice(HELP_AUDIO)
            logger.info(f"Playing help response: {audio_file}")
            play_audio(audio_file)
            return
        
        # Check for direct topic learning commands
        if any(phrase in text for phrase in ["teach me", "learn", "start", "play"]):
            for topic, config in TOPIC_CONFIG.items():
                if any(keyword in text for keyword in config["keywords"]):
                    logger.info(f"Direct topic request: {topic}")
                    play_audio(config["audio"])
                    launch_file(config["file"], topic)
                    return
        
        # Check for homework-related commands (triggers OCR)
        homework_keywords = ["homework", "exercise", "problem", "question", "solve", "assignment", "worksheet"]
        if any(keyword in text for keyword in homework_keywords):
            logger.info("Homework command detected - starting OCR process")
            
            # Capture and process image
            ocr_text = capture_and_process_image()
            
            if ocr_text:
                # Classify topic from OCR text
                identified_topic = classify_topic_from_text(ocr_text)
                
                if identified_topic:
                    logger.info(f"Topic identified: {identified_topic}")
                    play_audio(AUDIO_FILES.get("topic_found", ""))
                    
                    # Play topic-specific starting audio and launch file
                    config = TOPIC_CONFIG[identified_topic]
                    play_audio(config["audio"])
                    launch_file(config["file"], identified_topic)
                else:
                    logger.info("No matching topic found in homework")
                    play_audio(AUDIO_FILES.get("topic_not_found", ""))
            return
        
        # If no specific command matched
        logger.info(f"No matching command for: {text}")
        
    except sr.UnknownValueError:
        logger.debug("Could not understand audio")
        pass
    except sr.RequestError as e:
        logger.error(f"Speech recognition error: {e}")
        pass
    except Exception as e:
        logger.error(f"Callback error: {e}")
        pass

def main():
    """Main function."""
    
    
    print("Initializing Homi - Smart Study Assistant with Google Vision OCR and Servo Control")
    
    # Initialize servo
    setup_servo()
    
    # Check if required files exist
    if not os.path.exists("audio_files"):
        os.makedirs("audio_files")
        logger.warning("Created audio_files directory - please add your audio files")
    
    if not os.path.exists("keytoken.json"):
        logger.error("Google Cloud credentials file 'keytoken.json' not found!")
        print("Please ensure keytoken.json is in the same directory as this script.")
        cleanup_gpio()
        return
    
    # Test Google Vision API connectivity
    try:
        client = vision.ImageAnnotatorClient()
        logger.info("Google Vision API client initialized successfully")
        show_fullscreen_hello()
    except Exception as e:
        logger.error(f"Failed to initialize Google Vision API: {e}")
        print("Please check your Google Cloud credentials and internet connection.")
        cleanup_gpio()
        return
    
    # Initialize recognizer and microphone
    recognizer = sr.Recognizer()
    microphone = setup_microphone()
    
    if microphone is None:
        print("Failed to set up microphone. Exiting.")
        cleanup_gpio()
        return
    
    # Configure recognizer for Pi
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    
    # Adjust for ambient noise
    try:
        with microphone as source:
            print("Calibrating microphone... Please wait.")
            recognizer.adjust_for_ambient_noise(source, duration=3)
            print("Ready! Say 'Hello' to start, 'help me with homework' for OCR mode, or 'I am hungry' for feeding.")
    except Exception as e:
        logger.error(f"Microphone calibration failed: {e}")
        play_audio(AUDIO_FILES.get("error", ""))
    
    # Start listening
    try:
        stop_listening = recognizer.listen_in_background(microphone, callback, phrase_time_limit=5)
        play_audio(AUDIO_FILES.get("ready", ""))
        
        # Keep running
        while True:
            time.sleep(0.1)
            
            
    except KeyboardInterrupt:
        print("\nShutting down Homi...")
        stop_listening(wait_for_stop=False)
        logger.info("Stopped listening")
        play_audio(AUDIO_FILES.get("goodbye", ""))
        
        # Cleanup
        close_all_active_files()
        cleanup_gpio()
        
    except Exception as e:
        logger.error(f"Main loop error: {e}")
        play_audio(AUDIO_FILES.get("error", ""))
        cleanup_gpio()

    

if __name__ == "__main__":
    main()
