import cv2
from cvzone.HandTrackingModule import HandDetector
from picamera2 import Picamera2

# Initialize picamera2
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})  # Explicit RGB format
picam2.configure(config)
picam2.start()

# Initialize hand detector
detector = HandDetector(detectionCon=0.8, maxHands=2)

while True:
    # Capture frame as RGB numpy array
    img = picam2.capture_array()
    if img is None:
        continue  # Skip if no frame (rare)

    # Ensure frame is 3-channel RGB (remove alpha channel if present)
    if img.shape[2] == 4:  # Check for RGBA
        img = img[:, :, :3]  # Slice to keep only RGB channels

    # Flip horizontally for mirror effect (optional, matches typical webcam behavior)
    img = cv2.flip(img, 1)

    # Process hands (cvzone expects BGR, so convert here)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    hands, img_display = detector.findHands(img_bgr, draw=True)  # Draw=True to annotate on img_display

    totalFingers = 0
    if hands:
        for hand in hands:
            fingers = detector.fingersUp(hand)
            totalFingers += fingers.count(1)
        cv2.putText(img_display, f'Total Fingers: {totalFingers}', (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Finger Counter", img_display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
picam2.stop()
cv2.destroyAllWindows()
