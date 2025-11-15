import subprocess
import sys
import logging
import os

def launch_color_detection(fullscreen=True, filename="1colors.py"):
    """
    Launch the color detection script with fullscreen support
    
    Args:
        fullscreen (bool): Whether to launch in fullscreen mode
        filename (str): Path to the color detection script
    """
    python_cmd = sys.executable if sys.executable else "python3"
    
    # Build command line arguments
    args = [python_cmd, filename]
    
    if fullscreen:
        args.extend(["--fullscreen"])
    
    # Optional: Add custom keys (use single characters to avoid ord() error)
    # args.extend(["--exit-key=q", "--toggle-key=t"])
    
    try:
        # Create logger if not exists
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)
        
        active_subprocess = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        mode = "fullscreen" if fullscreen else "windowed"
        logger.info(f"Launched {filename} in {mode} mode with PID {active_subprocess.pid}")
        print(f"Started {filename} (PID: {active_subprocess.pid}) - Mode: {mode}")
        print("Press Ctrl+C in terminal to stop, or use exit key in application")
        
        return active_subprocess
        
    except FileNotFoundError:
        logger.error(f"Python executable not found: {python_cmd}")
        print(f"Error: Python not found at {python_cmd}")
        return None
    except Exception as e:
        logger.error(f"Failed to launch {filename}: {str(e)}")
        print(f"Error launching {filename}: {str(e)}")
        return None

def main():
    """Main launcher function"""
    # Launch in fullscreen mode
    process = launch_color_detection(fullscreen=True, filename="1colors.py")
    
    if process:
        try:
            # Wait for process to complete
            process.wait()
            print(f"Process {process.pid} finished with return code {process.returncode}")
        except KeyboardInterrupt:
            print("\nStopping application...")
            if process.poll() is None:  # Process still running
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            print("Process terminated")

if __name__ == "__main__":
    main()
