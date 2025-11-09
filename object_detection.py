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

# GPIO Pin Configuration - BALANCED BIN SERVOS (2 per bin)
RECYCLABLE_SERVO_PIN_1 = 17  # Recyclable bin - Servo 1
RECYCLABLE_SERVO_PIN_2 = 5  # Recyclable bin - Servo 2 (for balance)
LANDFILL_SERVO_PIN_1 = 18  # Landfill bin - Servo 1
LANDFILL_SERVO_PIN_2 = 6  # Landfill bin - Servo 2 (for balance)

# Gate servos (2 per gate)
GATE_PIN_1 = 19  # Gate 1 - Servo A
GATE_PIN_2 = 16  # Gate 1 - Servo B
GATE_PIN_3 = 22  # Gate 2 - Servo A
GATE_PIN_4 = 23  # Gate 2 - Servo B

# Servo angle configuration (adjust these values based on your servo and bin design)
SERVO_CLOSED_ANGLE = 90  # Bin closed position
SERVO_OPEN_ANGLE = 45  # Bin open position (adjust to 180 if servo rotates opposite direction)
GATE_CLOSED_ANGLE = 90  # Gate closed (blocks bottle)
GATE_OPEN_ANGLE = 45  # Gate open (lets bottle through)

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


def run_detection(conf_threshold=0.25, headless=False, enable_servo=False):
    """Run webcam detection with trained model"""
    print("\n📹 WASTE DETECTION")
    if headless:
        print("(HEADLESS MODE - Saving frames to disk)")
    if enable_servo:
        print("(SERVO MODE - Enabled with BALANCED BINS)")
    print("=" * 70)

    if not MODEL_PATH.exists():
        print(f"❌ Model not found at {MODEL_PATH}")
        print("\nPlease transfer your trained model:")
        print("  scp best.pt harry@<raspberry-pi-ip>:~/Hackathon/best.pt")
        return

    print(f"✓ Using: {MODEL_PATH}\n")
    model = YOLO(str(MODEL_PATH))

    # Initialize ALL servos (4 for bins + 4 for gates = 8 total)
    pwm_recycle1 = None
    pwm_recycle2 = None
    pwm_landfill1 = None
    pwm_landfill2 = None
    pwm_gate1 = None
    pwm_gate2 = None
    pwm_gate3 = None
    pwm_gate4 = None

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

                # Setup ALL GPIO pins
                GPIO.setup(RECYCLABLE_SERVO_PIN_1, GPIO.OUT)
                GPIO.setup(RECYCLABLE_SERVO_PIN_2, GPIO.OUT)
                GPIO.setup(LANDFILL_SERVO_PIN_1, GPIO.OUT)
                GPIO.setup(LANDFILL_SERVO_PIN_2, GPIO.OUT)
                GPIO.setup(GATE_PIN_1, GPIO.OUT)
                GPIO.setup(GATE_PIN_2, GPIO.OUT)
                GPIO.setup(GATE_PIN_3, GPIO.OUT)
                GPIO.setup(GATE_PIN_4, GPIO.OUT)

                # Create PWM instances for ALL servos (50Hz is standard for servos)
                pwm_recycle1 = GPIO.PWM(RECYCLABLE_SERVO_PIN_1, 50)
                pwm_recycle2 = GPIO.PWM(RECYCLABLE_SERVO_PIN_2, 50)
                pwm_landfill1 = GPIO.PWM(LANDFILL_SERVO_PIN_1, 50)
                pwm_landfill2 = GPIO.PWM(LANDFILL_SERVO_PIN_2, 50)
                pwm_gate1 = GPIO.PWM(GATE_PIN_1, 50)
                pwm_gate2 = GPIO.PWM(GATE_PIN_2, 50)
                pwm_gate3 = GPIO.PWM(GATE_PIN_3, 50)
                pwm_gate4 = GPIO.PWM(GATE_PIN_4, 50)

                # Start PWM on ALL servos
                pwm_recycle1.start(0)
                pwm_recycle2.start(0)
                pwm_landfill1.start(0)
                pwm_landfill2.start(0)
                pwm_gate1.start(0)
                pwm_gate2.start(0)
                pwm_gate3.start(0)
                pwm_gate4.start(0)

                # Initialize ALL servo positions
                print("Setting servos to initial positions...")
                print("  → Closing recyclable bin (both servos)...")
                set_servo_angle(pwm_recycle1, SERVO_CLOSED_ANGLE)
                set_servo_angle(pwm_recycle2, SERVO_CLOSED_ANGLE)
                print("  → Closing landfill bin (both servos)...")
                set_servo_angle(pwm_landfill1, SERVO_CLOSED_ANGLE)
                set_servo_angle(pwm_landfill2, SERVO_CLOSED_ANGLE)
                print("  → Closing all gates...")
                set_servo_angle(pwm_gate1, GATE_CLOSED_ANGLE)
                set_servo_angle(pwm_gate2, GATE_CLOSED_ANGLE)
                set_servo_angle(pwm_gate3, GATE_CLOSED_ANGLE)
                set_servo_angle(pwm_gate4, GATE_CLOSED_ANGLE)
                time.sleep(1)

                print("✓ All 8 servos initialized successfully!")
                print(f"\n  RECYCLABLE BIN (Balanced):")
                print(f"    Servo 1: GPIO {RECYCLABLE_SERVO_PIN_1}")
                print(f"    Servo 2: GPIO {RECYCLABLE_SERVO_PIN_2}")
                print(f"  LANDFILL BIN (Balanced):")
                print(f"    Servo 1: GPIO {LANDFILL_SERVO_PIN_1}")
                print(f"    Servo 2: GPIO {LANDFILL_SERVO_PIN_2}")
                print(f"  GATE 1:")
                print(f"    Servo A: GPIO {GATE_PIN_1}")
                print(f"    Servo B: GPIO {GATE_PIN_2}")
                print(f"  GATE 2:")
                print(f"    Servo A: GPIO {GATE_PIN_3}")
                print(f"    Servo B: GPIO {GATE_PIN_4}")
                print(f"\n  Bin closed: {SERVO_CLOSED_ANGLE}° | Bin open: {SERVO_OPEN_ANGLE}°")
                print(f"  Gate closed: {GATE_CLOSED_ANGLE}° | Gate open: {GATE_OPEN_ANGLE}°")
            except Exception as e:
                print(f"❌ Failed to initialize servos: {e}")
                enable_servo = False
                # Stop ALL PWM instances if initialization fails
                for pwm in [pwm_recycle1, pwm_recycle2, pwm_landfill1, pwm_landfill2,
                            pwm_gate1, pwm_gate2, pwm_gate3, pwm_gate4]:
                    if pwm:
                        pwm.stop()
                GPIO.cleanup()
                pwm_recycle1 = pwm_recycle2 = pwm_landfill1 = pwm_landfill2 = None
                pwm_gate1 = pwm_gate2 = pwm_gate3 = pwm_gate4 = None

    # Initialize camera - Try Picamera2 first, then fall back to cv2
    picam2 = None
    cap = None

    if PICAMERA2_AVAILABLE:
        try:
            print("\nInitializing Picamera2...")
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

    # Gate cycling state machine
    current_gate = 1  # Start with gate 1
    gate_state = "CLOSED"  # CLOSED, WAITING_CLEAR, OPENING, OPEN
    bin_open_duration = 2.5  # seconds to keep bin open
    clear_wait_time = 1.0  # seconds to wait after no detection before opening gate
    last_state_change = time.time()
    last_detection_time = 0

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

            # Gate cycling logic with BALANCED BIN CONTROL
            current_time = time.time()
            is_object_detected = (recyclable > 0) or (landfill > 0)

            if enable_servo and pwm_recycle1 is not None:
                if gate_state == "CLOSED":
                    # Gate is closed, bottle is stopped
                    if is_object_detected:
                        last_detection_time = current_time

                        # Classify and open appropriate bin (BOTH SERVOS MOVE TOGETHER)
                        if recyclable > 0 and landfill == 0:
                            print(f"♻️  RECYCLABLE detected at Gate {current_gate}! Opening BOTH recyclable servos")
                            # Open BOTH recyclable bin servos for balanced operation
                            set_servo_angle(pwm_recycle1, SERVO_OPEN_ANGLE)
                            set_servo_angle(pwm_recycle2, SERVO_OPEN_ANGLE)
                            # Keep landfill closed
                            set_servo_angle(pwm_landfill1, SERVO_CLOSED_ANGLE)
                            set_servo_angle(pwm_landfill2, SERVO_CLOSED_ANGLE)
                            time.sleep(bin_open_duration)
                            # Close BOTH recyclable bin servos
                            set_servo_angle(pwm_recycle1, SERVO_CLOSED_ANGLE)
                            set_servo_angle(pwm_recycle2, SERVO_CLOSED_ANGLE)

                        elif landfill > 0 and recyclable == 0:
                            print(f"🗑️  LANDFILL detected at Gate {current_gate}! Opening BOTH landfill servos")
                            # Open BOTH landfill bin servos for balanced operation
                            set_servo_angle(pwm_landfill1, SERVO_OPEN_ANGLE)
                            set_servo_angle(pwm_landfill2, SERVO_OPEN_ANGLE)
                            # Keep recyclable closed
                            set_servo_angle(pwm_recycle1, SERVO_CLOSED_ANGLE)
                            set_servo_angle(pwm_recycle2, SERVO_CLOSED_ANGLE)
                            time.sleep(bin_open_duration)
                            # Close BOTH landfill bin servos
                            set_servo_angle(pwm_landfill1, SERVO_CLOSED_ANGLE)
                            set_servo_angle(pwm_landfill2, SERVO_CLOSED_ANGLE)

                        elif recyclable > 0 and landfill > 0:
                            print(f"⚠️  Both types detected at Gate {current_gate} - keeping ALL bins closed")
                            # Keep ALL bin servos closed
                            set_servo_angle(pwm_recycle1, SERVO_CLOSED_ANGLE)
                            set_servo_angle(pwm_recycle2, SERVO_CLOSED_ANGLE)
                            set_servo_angle(pwm_landfill1, SERVO_CLOSED_ANGLE)
                            set_servo_angle(pwm_landfill2, SERVO_CLOSED_ANGLE)

                        gate_state = "WAITING_CLEAR"
                        last_state_change = current_time

                elif gate_state == "WAITING_CLEAR":
                    # Waiting for object to clear from view
                    if is_object_detected:
                        last_detection_time = current_time
                    else:
                        # No object detected, wait a bit to make sure it's really gone
                        if current_time - last_detection_time > clear_wait_time:
                            print(f"✓ Gate {current_gate} clear, opening gate...")
                            gate_state = "OPENING"
                            last_state_change = current_time

                elif gate_state == "OPENING":
                    # Open the current gate (BOTH SERVOS)
                    if current_gate == 1:
                        set_servo_angle(pwm_gate1, GATE_OPEN_ANGLE)
                        set_servo_angle(pwm_gate2, GATE_OPEN_ANGLE)
                    elif current_gate == 2:
                        set_servo_angle(pwm_gate3, GATE_OPEN_ANGLE)
                        set_servo_angle(pwm_gate4, GATE_OPEN_ANGLE)

                    print(f"🚪 Gate {current_gate} opened - bottle can pass")
                    gate_state = "OPEN"
                    last_state_change = current_time

                elif gate_state == "OPEN":
                    # Gate is open, wait a moment then close and switch to next gate
                    if current_time - last_state_change > 1.0:  # Keep gate open for 1 second
                        # Close current gate (BOTH SERVOS)
                        if current_gate == 1:
                            set_servo_angle(pwm_gate1, GATE_CLOSED_ANGLE)
                            set_servo_angle(pwm_gate2, GATE_CLOSED_ANGLE)
                            print(f"🚪 Gate 1 closed")
                            current_gate = 2  # Switch to gate 2
                        elif current_gate == 2:
                            set_servo_angle(pwm_gate3, GATE_CLOSED_ANGLE)
                            set_servo_angle(pwm_gate4, GATE_CLOSED_ANGLE)
                            print(f"🚪 Gate 2 closed")
                            current_gate = 1  # Switch back to gate 1

                        print(f"🔄 Ready for next bottle at Gate {current_gate}")
                        gate_state = "CLOSED"
                        last_state_change = current_time

            # Stats overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (300, 170), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

            cv2.putText(frame, f"Recyclable: {recyclable}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Landfill: {landfill}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Unknown: {unknown}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"Conf: {current_conf:.2f}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Gate: {current_gate} - {gate_state}", (10, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)

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
        # Cleanup - Close ALL servos
        if enable_servo and pwm_recycle1 is not None:
            print("\nCleaning up ALL servos...")
            print("  → Closing recyclable bin (both servos)...")
            set_servo_angle(pwm_recycle1, SERVO_CLOSED_ANGLE)
            set_servo_angle(pwm_recycle2, SERVO_CLOSED_ANGLE)
            print("  → Closing landfill bin (both servos)...")
            set_servo_angle(pwm_landfill1, SERVO_CLOSED_ANGLE)
            set_servo_angle(pwm_landfill2, SERVO_CLOSED_ANGLE)
            print("  → Closing all gates...")
            set_servo_angle(pwm_gate1, GATE_CLOSED_ANGLE)
            set_servo_angle(pwm_gate2, GATE_CLOSED_ANGLE)
            set_servo_angle(pwm_gate3, GATE_CLOSED_ANGLE)
            set_servo_angle(pwm_gate4, GATE_CLOSED_ANGLE)
            time.sleep(1)

            print("  → Stopping PWM on all servos...")
            pwm_recycle1.stop()
            pwm_recycle2.stop()
            pwm_landfill1.stop()
            pwm_landfill2.stop()
            pwm_gate1.stop()
            pwm_gate2.stop()
            pwm_gate3.stop()
            pwm_gate4.stop()
            GPIO.cleanup()
            print("✓ All 8 servos cleaned up")

        if picam2 is not None:
            picam2.stop()
            print("✓ Picamera2 stopped")
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("✓ Detection ended")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("RASPBERRY PI WASTE DETECTION SYSTEM - BALANCED BIN VERSION")
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