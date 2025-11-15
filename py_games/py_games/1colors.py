import cv2
import argparse
from picamera2 import Picamera2
import sys

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='PiCamera2 Color Detection with Fullscreen Support')
    parser.add_argument("--fullscreen", action="store_true", 
                       help="Run application in fullscreen mode")
    parser.add_argument("--exit-key", type=str, default="esc", 
                       help="Key to exit the application (default: esc)")
    parser.add_argument("--toggle-key", type=str, default="f", 
                       help="Key to toggle fullscreen (default: f)")
    return parser.parse_args()

def setup_window(window_name, fullscreen=False):
    """Setup window with fullscreen capability"""
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # Must be NORMAL for fullscreen support
    if fullscreen:
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)  # Keep on top (optional)
    return window_name

def toggle_fullscreen(window_name, current_state):
    """Toggle fullscreen on/off"""
    fullscreen_state = not current_state
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, 
                         cv2.WINDOW_FULLSCREEN if fullscreen_state else cv2.WINDOW_NORMAL)
    return fullscreen_state

def get_key_code(key_char):
    """Convert key character to OpenCV key code"""
    return ord(key_char.lower())

def main():
    # Parse command-line arguments
    args = parse_arguments()
    
    # Setup window BEFORE starting the camera
    window_name = "Color Detection"
    setup_window(window_name, args.fullscreen)
    
    fullscreen = args.fullscreen
    exit_key = get_key_code(args.exit_key)
    toggle_key = get_key_code(args.toggle_key)
    
    print(f"Fullscreen mode: {fullscreen}")
    print(f"Exit key: '{args.exit_key}' (ASCII: {exit_key})")
    if not fullscreen:
        print(f"Toggle fullscreen key: '{args.toggle_key}'")
    
    # Initialize picamera2
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (1280, 720), "format": "RGB888"})
    picam2.configure(config)
    picam2.start()
    
    try:
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
            
            # Add fullscreen status indicator
            status_text = f"Fullscreen: {'ON' if fullscreen else 'OFF'}"
            cv2.putText(frame_bgr, status_text, (10, height - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Display the frame
            cv2.imshow(window_name, frame_bgr)
            key = cv2.waitKey(1) & 0xFF
            
            if key == exit_key:
                print("Exit key pressed. Shutting down...")
                break
            elif key == toggle_key:
                fullscreen = toggle_fullscreen(window_name, fullscreen)
                print(f"Fullscreen toggled: {fullscreen}")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Cleanup
        picam2.stop()
        cv2.destroyAllWindows()
        print("Camera stopped and windows closed")

if __name__ == "__main__":
    main()
