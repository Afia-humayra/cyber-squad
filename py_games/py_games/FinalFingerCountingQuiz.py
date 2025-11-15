import cv2
from cvzone.HandTrackingModule import HandDetector
import random
import time

# -----------------------------
# Camera Initialization (Pi Safe)
# -----------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera not detected!")
    exit()

# Try to set resolution (some USB cams ignore)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Hand detector (Lower confidence = faster for Pi)
detector = HandDetector(detectionCon=0.7, maxHands=2)

# -----------------------------
# Game Variables
# -----------------------------
target_number = random.randint(1, 10)
score = 0
show_correct = False
last_correct_time = 0
SWITCH_DELAY = 1.5

game_over = False
END_DELAY = 3  # seconds to show "Well Done!" before closing

# -----------------------------
# Main Loop
# -----------------------------
while True:
    success, img = cap.read()
    if not success:
        print("Failed to read camera frame")
        break

    # Ensure stable resolution (Pi cameras sometimes fluctuate)
    img = cv2.resize(img, (800, 480))
    img = cv2.flip(img, 1)  # Mirror effect

    h, w, _ = img.shape

    # Detect hands
    hands, img = detector.findHands(img, flipType=False)

    # -----------------------------
    # Display Base Text
    # -----------------------------
    if not game_over:
        cv2.putText(img, f"Show me {target_number} fingers!", (30, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)
        cv2.putText(img, f"Score: {score}", (w - 200, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)

    total_fingers = 0

    # -----------------------------
    # Hand Processing
    # -----------------------------
    if hands and not game_over:

        for hand in hands:
            fingers = detector.fingersUp(hand)
            total_fingers += fingers.count(1)

        cv2.putText(img, f"You showed: {total_fingers}", (30, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

        # Correct Answer
        if total_fingers == target_number and not show_correct:
            score += 1
            show_correct = True
            last_correct_time = time.time()

        # Wrong Answer (but ignore 0 fingers)
        elif total_fingers != target_number and not show_correct and total_fingers != 0:
            cv2.putText(img, "Wrong!", (30, 180),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

    # -----------------------------
    # "Correct!" Display Timer
    # -----------------------------
    if show_correct and not game_over:
        cv2.putText(img, "Correct!", (30, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        if time.time() - last_correct_time > SWITCH_DELAY:
            target_number = random.randint(1, 10)
            show_correct = False

    # -----------------------------
    # Win Condition
    # -----------------------------
    if score >= 10 and not game_over:
        game_over = True
        end_time = time.time()

    if game_over:
        cv2.putText(img, "WELL DONE!", (int(w / 5), int(h / 2)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.7, (0, 255, 0), 5)

        if time.time() - end_time > END_DELAY:
            break

    # -----------------------------
    # Display
    # -----------------------------
    cv2.imshow("Finger Counting Quiz", img)
    cv2.resizeWindow("Finger Counting Quiz", 800, 480)

    if cv2.waitKey(1) == 27:  # ESC to quit
        break

# -----------------------------
# Cleanup
# -----------------------------
cap.release()
cv2.destroyAllWindows()
