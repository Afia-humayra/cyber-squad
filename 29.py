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
from datetime import datetime
import queue

# Initialize pygame mixer for audio playbook
pygame.mixer.init()

# Set Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'keytoken.json'

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track active subprocess for Python scripts and browser processes
active_subprocess = None
active_browser_processes = []
active_servo_process = None

# Shared queue for GUI updates
status_queue = queue.Queue()

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

# Servo configuration
SERVO_SCRIPT = "servo.py"

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
    "servo_moving": "audio_files/servo_moving.wav"
}

def update_status(message, status_type="info"):
    """Add status message to queue for GUI display."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_entry = {
        "timestamp": timestamp,
        "message": message,
        "type": status_type  # info, success, error, servo, listening
    }
    try:
        status_queue.put_nowait(status_entry)
    except queue.Full:
        pass  # Queue full, skip update

def log_with_gui(message, level=logging.INFO):
    """Enhanced logging that also updates GUI."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    logger.log(level, f"[{timestamp}] {message}")
    update_status(message, "info" if level == logging.INFO else "error")

def run_servo_script():
    """Run the servo.py script once with GUI feedback."""
    global active_servo_process
    
    log_with_gui("🔄 Starting servo movement...", logging.INFO)
    update_status("Moving Servo...", "servo")
    
    # Close any existing servo process
    if active_servo_process and active_servo_process.poll() is None:
        try:
            active_servo_process.terminate()
            active_servo_process.wait(timeout=2)
        except:
            active_servo_process.kill()
    
    try:
        if os.path.exists(SERVO_SCRIPT):
            python_cmd = sys.executable if sys.executable else "python3"
            active_servo_process = subprocess.Popen([python_cmd, SERVO_SCRIPT])
            log_with_gui(f"Started servo script PID: {active_servo_process.pid}", logging.INFO)
            
            play_audio(AUDIO_FILES.get("servo_moving", ""))
            
            time.sleep(3)
            if active_servo_process.poll() is None:
                active_servo_process.terminate()
                active_servo_process.wait(timeout=2)
                log_with_gui("Servo movement completed", logging.INFO)
            active_servo_process = None
            update_status("Servo Ready ✓", "success")
        else:
            error_msg = f"Servo script not found: {SERVO_SCRIPT}"
            log_with_gui(error_msg, logging.ERROR)
            update_status("Servo Error!", "error")
            play_audio(AUDIO_FILES.get("error", ""))
    except Exception as e:
        error_msg = f"Servo error: {e}"
        log_with_gui(error_msg, logging.ERROR)
        update_status("Servo Failed!", "error")
        active_servo_process = None
        play_audio(AUDIO_FILES.get("error", ""))

def show_dynamic_fullscreen_status():
    """Dynamic fullscreen display showing real-time status and logs."""
    
    def create_window():
        def exit_app(event=None):
            try:
                root.destroy()
                root.quit()
                log_with_gui("Fullscreen display closed")
            except Exception as e:
                logger.error(f"Error closing fullscreen: {e}")
        
        try:
            root = tk.Tk()
            root.title("Homi Status Monitor")
            
            # Ultra fullscreen configuration
            root.attributes('-fullscreen', True)
            root.overrideredirect(True)
            root.attributes('-topmost', True)
            root.configure(bg='black')
            root.resizable(False, False)
            
            # Bind exit keys
            exit_keys = ['q', 'Q', '<Escape>', '<Control-c>', '<Control-q>']
            for key in exit_keys:
                root.bind(key, exit_app)
            root.protocol("WM_DELETE_WINDOW", exit_app)
            
            root.focus_force()
            root.grab_set()
            
            # Main status frame
            main_frame = tk.Frame(root, bg='black')
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Status label (top, large)
            status_label = tk.Label(
                main_frame,
                text="🔸 Listening for Commands...",
                font=('Arial', 60, 'bold'),
                fg='#00FF00',
                bg='black'
            )
            status_label.pack(pady=(0, 20))
            
            # Log display frame
            log_frame = tk.Frame(main_frame, bg='black')
            log_frame.pack(fill='both', expand=True)
            
            # Log text widget with scrollbar
            log_text = tk.Text(
                log_frame,
                bg='black',
                fg='white',
                font=('Courier', 16),
                wrap='word',
                state='disabled',
                insertbackground='white'
            )
            scrollbar = tk.Scrollbar(log_frame, orient='vertical', command=log_text.yview)
            log_text.configure(yscrollcommand=scrollbar.set)
            
            log_text.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
            
            # Instructions
            instructions = tk.Label(
                main_frame,
                text="Press 'Q' or 'ESC' to exit | Voice Commands Active",
                font=('Arial', 18),
                fg='yellow',
                bg='black'
            )
            instructions.pack(side='bottom', pady=10)
            
            # Auto-scroll to bottom
            def scroll_to_bottom():
                log_text.see('end')
            
            # Update GUI from queue
            def update_gui():
                try:
                    while True:
                        status = status_queue.get_nowait()
                        # Update status label based on type
                        if status["type"] == "servo":
                            status_label.config(
                                text=f"⚙️ {status['message']}",
                                fg='#FFAA00'
                            )
                        elif status["type"] == "listening":
                            status_label.config(
                                text=f"🔸 {status['message']}",
                                fg='#00FF00'
                            )
                        elif status["type"] == "success":
                            status_label.config(
                                text=f"✅ {status['message']}",
                                fg='#00FF00'
                            )
                        elif status["type"] == "error":
                            status_label.config(
                                text=f"❌ {status['message']}",
                                fg='#FF0000'
                            )
                        else:
                            status_label.config(
                                text=f"📢 {status['message']}",
                                fg='#FFFFFF'
                            )
                        
                        # Add to log
                        log_text.config(state='normal')
                        log_text.insert('end', f"[{status['timestamp']}] {status['message']}\n")
                        log_text.config(state='disabled')
                        scroll_to_bottom()
                        
                        # Flash status label
                        original_fg = status_label.cget('fg')
                        status_label.config(fg='white')
                        root.after(200, lambda: status_label.config(fg=original_fg))
                        
                except queue.Empty:
                    pass
                
                # Schedule next update
                root.after(100, update_gui)
            
            # Initial status
            update_status("Homi Started - Listening for Commands", "listening")
            log_with_gui("Dynamic fullscreen status monitor initialized")
            
            # Start GUI update loop
            update_gui()
            
            # Initial log entries
            log_text.config(state='normal')
            log_text.insert('end', "=== Homi Smart Assistant Logs ===\n")
            log_text.config(state='disabled')
            scroll_to_bottom()
            
            root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
            root.update_idletasks()
            
            log_with_gui("Fullscreen status display started")
            root.mainloop()
            
        except Exception as e:
            logger.error(f"Fullscreen GUI error: {e}")
        finally:
            try:
                root.destroy()
            except:
                pass
    
    thread = threading.Thread(target=create_window, daemon=True)
    thread.start()

def play_audio(file_path):
    """Play an audio file using pygame."""
    try:
        if os.path.exists(file_path):
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            log_with_gui(f"Audio played: {os.path.basename(file_path)}")
        else:
            log_with_gui(f"Audio missing: {os.path.basename(file_path)}", logging.WARNING)
    except Exception as e:
        log_with_gui(f"Audio error: {e}", logging.ERROR)

def capture_image_with_camera(output_path='captured_homework.jpg', preview_delay=5000):
    """Captures an image using Raspberry Pi camera with GUI feedback."""
    update_status("📷 Preparing camera...", "info")
    try:
        log_with_gui("Opening camera preview...")
        subprocess.run([
            'rpicam-still', 
            '-o', output_path,
            '-t', str(preview_delay + 1000),
            '--width', '1920',
            '--height', '1080',
            '--preview', '0,0,640,480'
        ], check=True)
        log_with_gui(f"Image captured: {output_path}")
        update_status("📸 Photo captured!", "success")
        return output_path
    except Exception as e:
        log_with_gui(f"Camera error: {e}", logging.ERROR)
        update_status("Camera Failed!", "error")
        return None

def detect_text_from_file(image_file):
    """Detects text from image using Google Vision API."""
    update_status("🔍 Processing OCR...", "info")
    try:
        client = vision.ImageAnnotatorClient()
        with io.open(image_file, 'rb') as file:
            content = file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(response.error.message)
            
        if response.text_annotations:
            full_text = response.text_annotations[0].description
            log_with_gui(f"OCR detected: {full_text[:100]}...")
            update_status("✅ Text detected!", "success")
            return full_text.lower()
        else:
            log_with_gui("No text detected in image")
            return None
    except Exception as e:
        log_with_gui(f"OCR error: {e}", logging.ERROR)
        return None

# ... [Keep all other functions like classify_topic_from_text, launch_file, etc. unchanged until callback] ...

def callback(recognizer, audio):
    """Process voice commands with GUI feedback."""
    try:
        update_status("🎤 Processing voice...", "listening")
        text = recognizer.recognize_google(audio, language="en-US").lower()
        log_with_gui(f"Voice: '{text}'")
        
        # Hungry keyword
        hungry_keywords = ["hungry", "i'm hungry", "am hungry", "feeling hungry"]
        if any(keyword in text for keyword in hungry_keywords):
            log_with_gui("Hungry detected - activating servo!")
            run_servo_script()
            return
        
        # Close commands
        close_patterns = [
            ("close" in text and "game" in text),
            ("stop" in text and "game" in text),
            ("thank" in text and "you" in text),
            ("thanks" in text),
            ("close" in text), ("finish" in text), ("done" in text), ("exit" in text)
        ]
        
        if any(close_patterns):
            log_with_gui("Closing all sessions...")
            close_all_active_files()
            return
        
        # Greeting
        if any(word in text.split() for word in ["hello", "hi", "hey"]):
            update_status("👋 Greeting detected", "success")
            audio_file = random.choice(GREETING_AUDIO)
            play_audio(audio_file)
            return
        
        # Help
        if any(word in text for word in ["can", "help", "assist"]):
            update_status("❓ Help requested", "info")
            audio_file = random.choice(HELP_AUDIO)
            play_audio(audio_file)
            return
        
        # Homework/OCR
        homework_keywords = ["homework", "exercise", "problem", "question", "solve", "assignment", "worksheet"]
        if any(keyword in text for keyword in homework_keywords):
            log_with_gui("Homework detected - starting OCR")
            update_status("📚 Scanning homework...", "info")
            ocr_text = capture_and_process_image()
            if ocr_text:
                topic = classify_topic_from_text(ocr_text)
                if topic:
                    update_status(f"🎯 Topic: {topic}", "success")
                    config = TOPIC_CONFIG[topic]
                    play_audio(config["audio"])
                    launch_file(config["file"], topic)
                else:
                    update_status("No matching topic", "error")
                    play_audio(AUDIO_FILES.get("topic_not_found", ""))
            return
        
        log_with_gui(f"No command matched: {text}")
        
    except sr.UnknownValueError:
        pass
    except Exception as e:
        log_with_gui(f"Voice processing error: {e}", logging.ERROR)
    finally:
        update_status("🔸 Listening...", "listening")

def main():
    """Main function with dynamic status display."""
    print("Initializing Homi with Dynamic Status Display")
    
    # Check servo script
    if not os.path.exists(SERVO_SCRIPT):
        log_with_gui(f"Warning: {SERVO_SCRIPT} not found", logging.WARNING)
    
    # Check credentials
    if not os.path.exists("keytoken.json"):
        log_with_gui("ERROR: keytoken.json not found!", logging.ERROR)
        return
    
    # Initialize Vision API and start GUI
    try:
        client = vision.ImageAnnotatorClient()
        log_with_gui("Google Vision API ready")
        show_dynamic_fullscreen_status()  # Starts in background
        time.sleep(2)  # Let GUI initialize
    except Exception as e:
        log_with_gui(f"Vision API error: {e}", logging.ERROR)
        return
    
    # Setup microphone
    recognizer = sr.Recognizer()
    microphone = setup_microphone()
    if not microphone:
        log_with_gui("Microphone setup failed", logging.ERROR)
        return
    
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=3)
        log_with_gui("Microphone calibrated - Ready!")
        update_status("🔸 Listening for Commands...", "listening")
    
    # Start listening
    try:
        stop_listening = recognizer.listen_in_background(microphone, callback, phrase_time_limit=5)
        play_audio(AUDIO_FILES.get("ready", ""))
        
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        log_with_gui("Shutting down...")
    finally:
        try:
            stop_listening(wait_for_stop=False)
        except:
            pass
        close_all_active_files()

if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            GPIO.cleanup()
        except:
            pass
