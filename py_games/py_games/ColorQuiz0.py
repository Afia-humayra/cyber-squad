import cv2
from random import choice
import time

# ---------------------
# Camera Setup (Raspberry Pi Friendly)
# ---------------------
cap = cv2.VideoCapture(0)

# Force resolution (some cameras ignore, so we resize later)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def detect_color(h, s, v):
    """Return color name based on HSV pixel."""
    if v <= 50:
        return "Black"
    elif s <= 50 and v >= 200:
        return "White"
    elif s <= 50:
        return "Gray"
    else:
        if h < 5 or h >= 178:
            return "Red"
        elif h < 22:
            return "Orange"
        elif h < 33:
            return "Yellow"
        elif h < 78:
            return "Green"
        elif h < 131:
            return "Blue"
        elif h < 178:
            return "Violet"
        else:
            return "Red"


# ---------------------
# Game Variables
# ---------------------
colors = ["Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Black", "White", "Gray"]
score = 0
target_color = choice(colors)
last_switch_time = time.time()
QUIZ_DURATION = 5
game_over = False
END_DELAY = 3  # seconds after win before exit


# ---------------------
# Game Loop
# ---------------------
while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera read failed")
        break

    # Ensure correct size even if camera ignores resolution
    frame = cv2.resize(frame, (800, 480))

    # HSV conversion
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    height, width, _ = frame.shape
    cx, cy = width // 2, height // 2

    # Pixel at center
    h, s, v = hsv_frame[cy, cx]
    detected_color = detect_color(h, s, v)

    # Show central crosshair
    cv2.circle(frame, (cx, cy), 10, (255, 0, 0), 3)

    if not game_over:
        # Display info
        cv2.putText(frame, f"Target: {target_color}", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Detected: {detected_color}", (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, f"Score: {score}", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        # Feedback text
        if detected_color == target_color:
            cv2.putText(frame, "Right!", (20, 210),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        else:
            cv2.putText(frame, "Try Again!", (20, 210),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        # Check if it's time to switch question
        if time.time() - last_switch_time > QUIZ_DURATION:
            if detected_color == target_color:
                score += 1
                if score >= 10:
                    game_over = True
                    end_time = time.time()

            target_color = choice(colors)
            last_switch_time = time.time()

    else:
        # WIN SCREEN
        cv2.putText(frame, "  WELL DONE!", (width // 5, height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 5)

        if time.time() - end_time > END_DELAY:
            break

    # Show Window
    cv2.imshow("Color Quiz", frame)

    # ESC to quit
    if cv2.waitKey(1) == 27:
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
