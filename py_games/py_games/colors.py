import cv2
from random import choice
import time

# Set up the camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def detect_color(h, s, v):
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

colors = ["Red", "Orange", "Yellow", "Green", "Blue", "Violet", "Black", "White", "Gray"]
score = 0
target_color = choice(colors)
last_switch_time = time.time()
QUIZ_DURATION = 5
game_over = False
END_DELAY = 3  # seconds before ending after winning

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Resize just in case the camera doesn’t natively support 800x480
    frame = cv2.resize(frame, (800, 480))

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    height, width, _ = frame.shape
    cx, cy = width // 2, height // 2
    pixel = hsv_frame[cy, cx]
    h, s, v = pixel[0], pixel[1], pixel[2]
    detected_color = detect_color(h, s, v)

    cv2.circle(frame, (cx, cy), 10, (255, 0, 0), 3)

    if not game_over:
        cv2.putText(frame, f"Target: {target_color}", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Detected: {detected_color}", (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, f"Score: {score}", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        if detected_color == target_color:
            cv2.putText(frame, "Right!", (20, 210),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        else:
            cv2.putText(frame, "Try Again!", (20, 210),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        # Check every QUIZ_DURATION seconds
        if time.time() - last_switch_time > QUIZ_DURATION:
            if detected_color == target_color:
                score += 1
                if score >= 10:
                    game_over = True
                    end_time = time.time()
            target_color = choice(colors)
            last_switch_time = time.time()
    else:
        # Show winning message
        cv2.putText(frame, "  WELL DONE!", (width // 5, height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 5)


        if time.time() - end_time > END_DELAY:
            break

    cv2.imshow("Color Quiz", frame)

    key = cv2.waitKey(1)
    if key == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
