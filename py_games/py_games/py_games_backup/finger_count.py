import cv2
from cvzone.HandTrackingModule import HandDetector

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

detector = HandDetector(detectionCon=0.8, maxHands=2)

while True:
    success, img = cap.read()
    if not success:
        print("Failed to grab frame")
        break

    hands, img = detector.findHands(img)

    totalFingers = 0

    if hands:
        for hand in hands:
            fingers = detector.fingersUp(hand)
            totalFingers += fingers.count(1)

        cv2.putText(img, f'Total Fingers: {totalFingers}', (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Finger Counter", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
