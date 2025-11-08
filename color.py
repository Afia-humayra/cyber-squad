import cv2
from picamera2 import Picamera2

# Initialize picamera2
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (1280, 720), "format": "RGB888"})  # Set resolution and RGB format
picam2.configure(config)
picam2.start()

while True:
    # Capture frame as RGB numpy array
    frame = picam2.capture_array()
    if frame is None:
        continue  # Skip if no frame (rare)

    # Ensure frame is 3-channel RGB (remove alpha channel if present)
    if frame.shape[2] == 4:  # Check for RGBA
        frame = frame[:, :, :3]  # Slice to keep only RGB channels

    # Convert to BGR for OpenCV processing and display
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # Convert to HSV for color detection
    hsv_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    height, width, _ = frame_bgr.shape
    cx = int(width / 2)
    cy = int(height / 2)
    pixel_center = hsv_frame[cy, cx]
    hue_value = pixel_center[0]
    s = pixel_center[1]
    v = pixel_center[2]

    # Determine color
    if v <= 50:
        color = "Black"
    elif s <= 50 and v >= 200:
        color = "White"
    elif s <= 50:
        color = "Gray"
    else:
        if hue_value < 5 or hue_value >= 178:
            color = "Red"
        elif hue_value < 22:
            color = "Orange"
        elif hue_value < 33:
            color = "Yellow"
        elif hue_value < 78:
            color = "Green"
        elif hue_value < 131:
            color = "Blue"
        elif hue_value < 178:
            color = "Violet"
        else:
            color = "Red"

    # Draw text and circle on frame
    cv2.putText(frame_bgr, color, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.circle(frame_bgr, (cx, cy), 5, (255, 0, 0), 3)

    # Display the frame
    cv2.imshow('frame', frame_bgr)
    key = cv2.waitKey(1)
    if key == 27:  # ESC key
        break

# Cleanup
picam2.stop()
cv2.destroyAllWindows()
