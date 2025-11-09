from ultralytics import YOLO
import cv2
from pathlib import Path
import time

# Try to import picamera2 for Raspberry Pi camera support
try:
    from picamera2 import Picamera2

    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("⚠ Warning: picamera2 not available, will try standard cv2")

# Try to import GPIO for servo control
try:
    import RPi.GPIO as GPIO

    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠ Warning: RPi.GPIO not available, servo control disabled")

# GPIO Pin Configuration
RECYCLABLE_SERVO_PIN = 17
LANDFILL_SERVO_PIN = 18

# Servo angle configuration (adjust these values based on your servo and bin design)
SERVO_CLOSED_ANGLE = 45  # Closed position
SERVO_OPEN_ANGLE = 90  # Open position (adjust to 180 if servo rotates opposite direction)

# Model path
MODEL_PATH = Path('/home/harry/Hackathon/best.pt')

# Categories
RECYCLABLE_ITEMS = ['bottle-glass', 'bottle-plastic', 'tin can', 'gym bottle']
LANDFILL_ITEMS = ['cup-disposable', 'glass-wine', 'glass-normal', 'glass-mug', 'cup-handle']


def classify_waste_type(class_name):
    """Classify detected object"""
    class_lower = class_name.lower()
    if class_lower in [item.lower() for item in RECYCLABLE_ITEMS]:
        return "RECYCLABLE", (0, 255, 0)
    elif class_lower in [item.lower() for item in LANDFILL_ITEMS]:
        return "LANDFILL", (0, 0, 255)
    else:
        return "UNKNOWN", (255, 255, 0)


def set_servo_angle(pwm, angle):
    """
    Set servo to specific angle (0-180 degrees)
    Most servos: 0° = 2.5% duty, 90° = 7.5% duty, 180° = 12.5% duty
    """
    duty = 2.5 + (angle / 180.0) * 10.0
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)  # Wait for servo to reach position
    pwm.ChangeDutyCycle(0)  # Stop PWM signal to prevent jitter


def run_detection(conf_threshold=0.6, headless=False, enable_servo=False):
    """Run webcam detection with trained model"""
    print("\n📹 WASTE DETECTION")
    if headless:
        print("(HEADLESS MODE - Saving frames to disk)")
    if enable_servo:
        print("(SERVO MODE - Enabled)")
    print("=" * 70)

    if not MODEL_PATH.exists():
        print(f"❌ Model not found at {MODEL_PATH}")
        print("\nPlease transfer your trained model:")
        print("  scp best.pt harry@<raspberry-pi-ip>:~/Hackathon/best.pt")
        return

    print(f"✓ Using: {MODEL_PATH}\n")
    model = YOLO(str(MODEL_PATH))

    # Initialize servos if enabled
    pwm_recycle = None
    pwm_landfill = None

    if enable_servo:
        if not GPIO_AVAILABLE:
            print("❌ GPIO not available. Servo control disabled.")
            print("Install: sudo apt-get install python3-rpi.gpio")
            enable_servo = False
        else:
            try:
                print("Initializing servos...")
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)

                # Setup GPIO pins
                GPIO.setup(RECYCLABLE_SERVO_PIN, GPIO.OUT)
                GPIO.setup(LANDFILL_SERVO_PIN, GPIO.OUT)

                # Create PWM instances (50Hz is standard for servos)
                pwm_recycle = GPIO.PWM(RECYCLABLE_SERVO_PIN, 50)
                pwm_landfill = GPIO.PWM(LANDFILL_SERVO_PIN, 50)

                # Start PWM
                pwm_recycle.start(0)
                pwm_landfill.start(0)

                # Initialize servo positions (both closed)
                print("Setting servos to closed position...")
                set_servo_angle(pwm_recycle, SERVO_CLOSED_ANGLE)
                set_servo_angle(pwm_landfill, SERVO_CLOSED_ANGLE)
                time.sleep(1)

                print("✓ Servos initialized")
                print(f"  Recyclable servo: GPIO {RECYCLABLE_SERVO_PIN}")
                print(f"  Landfill servo: GPIO {LANDFILL_SERVO_PIN}")
                print(f"  Closed angle: {SERVO_CLOSED_ANGLE}°")
                print(f"  Open angle: {SERVO_OPEN_ANGLE}°")
            except Exception as e:
                print(f"❌ Failed to initialize servos: {e}")
                enable_servo = False
                if pwm_recycle:
                    pwm_recycle.stop()
                if pwm_landfill:
                    pwm_landfill.stop()
                GPIO.cleanup()
                pwm_recycle = None
                pwm_landfill = None

    # Initialize camera - Try Picamera2 first, then fall back to cv2
    picam2 = None
    cap = None

    if PICAMERA2_AVAILABLE:
        try:
            print("Initializing Picamera2...")
            picam2 = Picamera2()
            config = picam2.create_preview_configuration(
                main={"size": (1280, 720), "format": "RGB888"}
            )
            picam2.configure(config)
            picam2.start()
            time.sleep(2)
            print("✓ Picamera2 initialized successfully")
        except Exception as e:
            print(f"⚠ Picamera2 failed: {e}")
            print("Falling back to OpenCV...")
            picam2 = None

    # Fall back to OpenCV if Picamera2 not available or failed
    if picam2 is None:
        print("Trying OpenCV VideoCapture...")
        for device in [0, 1, 2]:
            test_cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
            if test_cap.isOpened():
                ret, frame = test_cap.read()
                if ret and frame is not None:
                    print(f"✓ Camera opened on device {device}")
                    cap = test_cap
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    break
                test_cap.release()

        if cap is None:
            print("❌ Could not open camera")
            print("\nTroubleshooting:")
            print("  1. Check camera connection")
            print("  2. Run: libcamera-hello --list-cameras")
            print("  3. Install: sudo apt-get install python3-picamera2")
            return

    print("\nCONTROLS: q=Quit | s=Screenshot | +/-=Confidence")
    if headless:
        print("Note: Running headless. Press Ctrl+C to stop.")
        print("Frames saved to: ~/Hackathon/detections/")
        import os
        os.makedirs('detections', exist_ok=True)
    print("=" * 70 + "\n")

    current_conf = conf_threshold
    frame_count = 0
    save_interval = 30 if headless else 0

    # Servo control variables
    last_detection_time = 0
    detection_cooldown = 3  # seconds between servo activations
    bin_open_duration = 2.5  # seconds to keep bin open

    try:
        while True:
            # Get frame from camera
            if picam2 is not None:
                frame = picam2.capture_array()
                ret = True
            else:
                ret, frame = cap.read()

            if not ret or frame is None:
                print("Failed to grab frame")
                break

            frame_count += 1

            recyclable = landfill = unknown = 0
            results = model(frame, conf=current_conf, verbose=False)

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls_id = int(box.cls[0])
                    class_name = model.names[cls_id]
                    confidence = float(box.conf[0])

                    waste_type, color = classify_waste_type(class_name)

                    if waste_type == "RECYCLABLE":
                        recyclable += 1
                    elif waste_type == "LANDFILL":
                        landfill += 1
                    else:
                        unknown += 1

                    # Draw box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    # Simple label: just waste type and confidence
                    label = f"{waste_type} {confidence:.0%}"

                    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(frame, (x1, y1 - h - 8), (x1 + w + 4, y1), color, -1)
                    cv2.putText(frame, label, (x1 + 2, y1 - 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Servo control logic
            current_time = time.time()
            if enable_servo and pwm_recycle is not None:
                if current_time - last_detection_time > detection_cooldown:
                    if recyclable > 0 and landfill == 0:
                        print(f"♻️  RECYCLABLE detected! Opening recyclable bin")
                        set_servo_angle(pwm_recycle, SERVO_OPEN_ANGLE)
                        set_servo_angle(pwm_landfill, SERVO_CLOSED_ANGLE)
                        time.sleep(bin_open_duration)
                        set_servo_angle(pwm_recycle, SERVO_CLOSED_ANGLE)
                        last_detection_time = current_time

                    elif landfill > 0 and recyclable == 0:
                        print(f"🗑️  LANDFILL detected! Opening landfill bin")
                        set_servo_angle(pwm_landfill, SERVO_OPEN_ANGLE)
                        set_servo_angle(pwm_recycle, SERVO_CLOSED_ANGLE)
                        time.sleep(bin_open_duration)
                        set_servo_angle(pwm_landfill, SERVO_CLOSED_ANGLE)
                        last_detection_time = current_time

                    elif recyclable > 0 and landfill > 0:
                        print("⚠️  Both types detected - keeping bins closed")
                        set_servo_angle(pwm_recycle, SERVO_CLOSED_ANGLE)
                        set_servo_angle(pwm_landfill, SERVO_CLOSED_ANGLE)

            # Stats overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (280, 140), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

            cv2.putText(frame, f"Recyclable: {recyclable}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Landfill: {landfill}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Unknown: {unknown}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"Conf: {current_conf:.2f}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Headless mode: save frames periodically
            if headless:
                total_detections = recyclable + landfill
                if total_detections > 0 or (frame_count % save_interval == 0):
                    filename = f'detections/frame_{frame_count:06d}.jpg'
                    cv2.imwrite(filename, frame)
                    if total_detections > 0:
                        print(f"Frame {frame_count}: R={recyclable} L={landfill} - Saved")
            else:
                # Display mode
                cv2.imshow('Waste Detection', frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break
                elif key == ord('s'):
                    filename = f'screenshot_{frame_count}.jpg'
                    cv2.imwrite(filename, frame)
                    print(f"✓ Screenshot saved: {filename}")
                elif key == ord('+') or key == ord('='):
                    current_conf = min(0.95, current_conf + 0.05)
                    print(f"Confidence: {current_conf:.2f}")
                elif key == ord('-'):
                    current_conf = max(0.05, current_conf - 0.05)
                    print(f"Confidence: {current_conf:.2f}")

    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped by user")
    finally:
        # Cleanup
        if enable_servo and pwm_recycle is not None:
            print("\nCleaning up servos...")
            set_servo_angle(pwm_recycle, SERVO_CLOSED_ANGLE)
            set_servo_angle(pwm_landfill, SERVO_CLOSED_ANGLE)
            time.sleep(1)
            pwm_recycle.stop()
            pwm_landfill.stop()
            GPIO.cleanup()
            print("✓ Servos cleaned up")

        if picam2 is not None:
            picam2.stop()
            print("✓ Picamera2 stopped")
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("✓ Detection ended")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("RASPBERRY PI WASTE DETECTION SYSTEM")
    print("=" * 70)

    while True:
        print("\n1. Run detection (with display)")
        print("2. Run detection (headless - no display)")
        print("3. Run detection + servo control (with display)")
        print("4. Run detection + servo control (headless)")
        print("0. Exit")

        choice = input("\nChoice (0-4): ").strip()

        try:
            if choice == '1':
                run_detection(headless=False, enable_servo=False)
            elif choice == '2':
                run_detection(headless=True, enable_servo=False)
            elif choice == '3':
                run_detection(headless=False, enable_servo=True)
            elif choice == '4':
                run_detection(headless=True, enable_servo=True)
            elif choice == '0':
                print("\nExiting...")
                break
            else:
                print("Invalid choice!")
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")

        if choice != '0':
            input("\nPress ENTER to continue...")