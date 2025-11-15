import cv2
import mediapipe as mp
import random
import time

# Initialize Mediapipe modules
mp_face_mesh = mp.solutions.face_mesh
mp_hands = mp.solutions.hands

face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)
hands = mp_hands.Hands(max_num_hands=1)

# Set up webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Force camera resolution to 800x480
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Body parts and their face mesh landmark indices
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

# Game settings
DIST_THRESHOLD = 40
STABILITY_FRAMES = 10
stable_counter = 0
GRACE_PERIOD = 1.5
just_switched = True
score = 0
game_over = False
END_DELAY = 3  # seconds to show "Well Done!" before ending

def euclidean_distance(p1, p2):
    return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) ** 0.5

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Resize to fixed display size (800x480)
    frame = cv2.resize(frame, (800, 480))
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_results = face_mesh.process(rgb)
    hand_results = hands.process(rgb)

    if not game_over:
        cv2.putText(frame, f"Show me your {current_question}!", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)
        cv2.putText(frame, f"Score: {score}", (w - 200, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)

    if just_switched and not game_over and time.time() - last_switch_time < GRACE_PERIOD:
        cv2.imshow("Body Parts Quiz", frame)
        cv2.resizeWindow("Body Parts Quiz", 800, 480)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue
    else:
        just_switched = False

    if face_results.multi_face_landmarks and hand_results.multi_hand_landmarks and not game_over:
        face_landmarks = face_results.multi_face_landmarks[0]
        target_idx = body_parts[current_question]
        target_lm = face_landmarks.landmark[target_idx]
        target_xy = (int(target_lm.x * w), int(target_lm.y * h))
        cv2.circle(frame, target_xy, 6, (0, 0, 255), -1)

        finger_tip_lm = hand_results.multi_hand_landmarks[0].landmark[8]
        finger_xy = (int(finger_tip_lm.x * w), int(finger_tip_lm.y * h))
        cv2.circle(frame, finger_xy, 8, (0, 255, 0), -1)

        dist = euclidean_distance(finger_xy, target_xy)

        if dist < DIST_THRESHOLD:
            stable_counter += 1
            cv2.putText(frame, "Correct!", (30, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        else:
            stable_counter = 0
            cv2.putText(frame, "Wrong!", (30, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        if stable_counter >= STABILITY_FRAMES:
            if time.time() - last_switch_time > 1:
                score += 1
                stable_counter = 0
                if score >= 10:
                    game_over = True
                    end_time = time.time()
                else:
                    current_question = random.choice(list(body_parts.keys()))
                    last_switch_time = time.time()
                    just_switched = True

    # Game Over message
    if game_over:
        cv2.putText(frame, "WELL DONE!", (int(w / 4), int(h / 2)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 5)

        if time.time() - end_time > END_DELAY:
            break

    cv2.imshow("Body Parts Quiz", frame)
    cv2.resizeWindow("Body Parts Quiz", 800, 480)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
