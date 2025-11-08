import cv2
import mediapipe as mp
import random
import time
from picamera2 import Picamera2
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
mp_hands = mp.solutions.hands

face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)
hands = mp_hands.Hands(max_num_hands=1)

body_parts = {
    "left eye": 33,
    "right eye": 263,
    "nose": 1,
    "mouth": 13,
    "left ear": 234,
    "right ear": 454
}

current_question = random.choice(list(body_parts.keys()))
last_switch_time = time.time()
show_homework = False
homework_start_time = time.time()

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()

def euclidean_distance(p1, p2):
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

while True:
    try:
        # Capture frame
        frame_rgb = picam2.capture_array()
        if frame_rgb is None:
            continue

        # Ensure the frame is a valid numpy array
        if not isinstance(frame_rgb, np.ndarray):
            print("Frame is not a numpy array")
            continue

        # Handle RGBA format if present
        if len(frame_rgb.shape) == 3 and frame_rgb.shape[2] == 4:  
            frame_rgb = frame_rgb[:, :, :3]  # Keep only RGB channels

        # Ensure frame is contiguous in memory
        frame_rgb = np.ascontiguousarray(frame_rgb)
        
        # Flip horizontally for mirror effect
        frame_rgb = cv2.flip(frame_rgb, 1)
        h, w = frame_rgb.shape[:2]

        # Process frame with MediaPipe (expects RGB)
        face_results = face_mesh.process(frame_rgb)
        hand_results = hands.process(frame_rgb)

        # Convert to BGR for OpenCV display
        frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        
        # Ensure frame is contiguous after color conversion
        frame = np.ascontiguousarray(frame)
        
        # Show homework message for first 5 seconds
        if show_homework and time.time() - homework_start_time < 5:
            cv2.putText(frame, "Show me your Home Work", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)
        else:
            show_homework = False
            cv2.putText(frame, f"Show me your {current_question}!", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)

        if face_results.multi_face_landmarks and hand_results.multi_hand_landmarks:
            face_landmarks = face_results.multi_face_landmarks[0]
            target_idx = body_parts[current_question]
            target_lm = face_landmarks.landmark[target_idx]
            target_xy = (int(target_lm.x * w), int(target_lm.y * h))

            # Draw target circle
            cv2.circle(frame, target_xy, 6, (0, 0, 255), -1)

            # Get finger tip position
            finger_tip_lm = hand_results.multi_hand_landmarks[0].landmark[8]
            finger_xy = (int(finger_tip_lm.x * w), int(finger_tip_lm.y * h))
            cv2.circle(frame, finger_xy, 8, (0, 255, 0), -1)

            # Check if finger is close to target
            distance = euclidean_distance(finger_xy, target_xy)
            if distance < 40:
                cv2.putText(frame, "Correct!", (30, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                # Switch to next question after 2 seconds
                if time.time() - last_switch_time > 2:
                    current_question = random.choice(list(body_parts.keys()))
                    last_switch_time = time.time()
            else:
                cv2.putText(frame, "Try again!", (30, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        # Display the frame
        cv2.imshow("Body Parts Quiz", frame)
        
        # Break on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    except Exception as e:
        print(f"Error: {e}")
        continue

# Cleanup
picam2.stop()
cv2.destroyAllWindows()
