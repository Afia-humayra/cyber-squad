import cv2
import mediapipe as mp
import random
import time

# -----------------------------
# Mediapipe Setup (Pi Optimized)
# -----------------------------
mp_face_mesh = mp.solutions.face_mesh
mp_hands = mp.solutions.hands

# Lower model complexity = faster for Raspberry Pi
face_mesh = mp_face_mesh.FaceMesh(
    refine_landmarks=True,
    max_num_faces=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# -----------------------------
# Camera Setup
# -----------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Force cam resolution (some cams ignore)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# -----------------------------
# Game Data
# -----------------------------
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

DIST_THRESHOLD = 40
STABILITY_FRAMES = 10
stable_counter = 0
GRACE_PERIOD = 1.5
just_switched = True

score = 0
game_over = False
END_DELAY = 3

# -----------------------------
# Helper Function
# -----------------------------
def euclidean_distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5


# -----------------------------
# Main Loop
# -----------------------------
while cap.isOpened():

    ret, frame = cap.read()
    if not ret:
        break

    # Ensure stable 800×480 output
    frame = cv2.resize(frame, (800, 480))
    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_results = face_mesh.process(rgb)
    hand_results = hands.process(rgb)

    # -----------------------------
    # Info Display
    # -----------------------------
    if not game_over:
        cv2.putText(frame, f"Touch your {current_question}!", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)
        cv2.putText(frame, f"Score: {score}", (w - 200, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)

    # Grace period after switching question
    if just_switched and not game_over and time.time() - last_switch_time < GRACE_PERIOD:
        cv2.imshow("Body Parts Quiz", frame)
        cv2.resizeWindow("Body Parts Quiz", 800, 480)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue
    else:
        just_switched = False

    # -----------------------------
    # Detection Logic
    # -----------------------------
    if face_results.multi_face_landmarks and hand_results.multi_hand_landmarks and not game_over:

        face_landmarks = face_results.multi_face_landmarks[0]

        # Target face landmark
        target_index = body_parts[current_question]
        lm = face_landmarks.landmark[target_index]
        target_xy = (int(lm.x * w), int(lm.y * h))
        cv2.circle(frame, target_xy, 6, (0, 0, 255), -1)

        # Hand fingertip (index finger)
        fingertip = hand_results.multi_hand_landmarks[0].landmark[8]
        finger_xy = (int(fingertip.x * w), int(fingertip.y * h))
        cv2.circle(frame, finger_xy, 8, (0, 255, 0), -1)

        # Distance check
        dist = euclidean_distance(finger_xy, target_xy)

        if dist < DIST_THRESHOLD:
            stable_counter += 1
            cv2.putText(frame, "Correct!", (30, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        else:
            stable_counter = 0
            cv2.putText(frame, "Wrong!", (30, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        # Enough stability → correct
        if stable_counter >= STABILITY_FRAMES:
            if time.time() - last_switch_time > 1:
                score += 1
                stable_counter = 0

                # WIN condition
                if score >= 10:
                    game_over = True
                    end_time = time.time()
                else:
                    current_question = random.choice(list(body_parts.keys()))
                    last_switch_time = time.time()
                    just_switched = True

    # -----------------------------
    # Game Over Screen
    # -----------------------------
    if game_over:
        cv2.putText(frame, "WELL DONE!", (int(w / 4), int(h / 2)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.7, (0, 255, 0), 5)

        if time.time() - end_time > END_DELAY:
            break

    # -----------------------------
    # Show Window
    # -----------------------------
    cv2.imshow("Body Parts Quiz", frame)
    cv2.resizeWindow("Body Parts Quiz", 800, 480)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
