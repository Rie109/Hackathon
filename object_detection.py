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
RECYCLABLE_SERVO_PIN_1 = 17  # Recyclable bin - Servo 1
RECYCLABLE_SERVO_PIN_2 = 5  # Recyclable bin - Servo 2
LANDFILL_SERVO_PIN_1 = 18  # Landfill bin - Servo 1
LANDFILL_SERVO_PIN_2 = 6  # Landfill bin - Servo 2

# Gate servos (2 per gate)
GATE_PIN_1 = 19  # Gate 1 - Servo A
GATE_PIN_2 = 16  # Gate 1 - Servo B
GATE_PIN_3 = 22  # Gate 2 - Servo A
GATE_PIN_4 = 23  # Gate 2 - Servo B

# Servo angle configuration
SERVO_CLOSED_ANGLE_LAND = 65
SERVO_OPEN_ANGLE_LAND = 150
SERVO_CLOSED_ANGLE_RECYCLE = 90
SERVO_OPEN_ANGLE_RECYCLE = 110
GATE_CLOSED_ANGLE_G1 = 120
GATE_OPEN_ANGLE_G1 = 180
GATE_CLOSED_ANGLE_G2 = 85
GATE_OPEN_ANGLE_G2 = 0

# Timing configuration
BIN_OPEN_DURATION = 2.5  # Time bin stays open
GATE_OPEN_DURATION = 2.0  # Time gate stays open
CLEAR_WAIT_TIME = 1.5  # Wait time after detection clears
IDLE_SLEEP_TIME = 3.0  # Sleep when both gates open but nothing detected

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
    """Set servo to specific angle (0-180 degrees)"""
    duty = 2.5 + (angle / 180.0) * 10.0
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)


def set_servo_pair(pwm1, pwm2, angle):
    """Set a pair of servos to the same angle"""
    set_servo_angle(pwm1, angle)
    set_servo_angle(pwm2, angle)


def run_detection(conf_threshold=0.25, headless=False, enable_servo=False):
    """Run webcam detection with trained model"""
    print("\n📹 WASTE DETECTION - SEQUENTIAL GATE LOGIC")
    if headless:
        print("(HEADLESS MODE - Saving frames to disk)")
    if enable_servo:
        print("(SERVO MODE - Enabled)")
    print("=" * 70)

    if not MODEL_PATH.exists():
        print(f"❌ Model not found at {MODEL_PATH}")
        return

    print(f"✓ Using: {MODEL_PATH}\n")
    model = YOLO(str(MODEL_PATH))

    # Initialize servo variables
    pwm_recycle1 = pwm_recycle2 = pwm_landfill1 = pwm_landfill2 = None
    pwm_gate1 = pwm_gate2 = pwm_gate3 = pwm_gate4 = None

    if enable_servo:
        if not GPIO_AVAILABLE:
            print("❌ GPIO not available. Servo control disabled.")
            enable_servo = False
        else:
            try:
                print("Initializing servos...")
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)

                # Setup all GPIO pins
                for pin in [RECYCLABLE_SERVO_PIN_1, RECYCLABLE_SERVO_PIN_2,
                            LANDFILL_SERVO_PIN_1, LANDFILL_SERVO_PIN_2,
                            GATE_PIN_1, GATE_PIN_2, GATE_PIN_3, GATE_PIN_4]:
                    GPIO.setup(pin, GPIO.OUT)

                # Create PWM instances
                pwm_recycle1 = GPIO.PWM(RECYCLABLE_SERVO_PIN_1, 50)
                pwm_recycle2 = GPIO.PWM(RECYCLABLE_SERVO_PIN_2, 50)
                pwm_landfill1 = GPIO.PWM(LANDFILL_SERVO_PIN_1, 50)
                pwm_landfill2 = GPIO.PWM(LANDFILL_SERVO_PIN_2, 50)
                pwm_gate1 = GPIO.PWM(GATE_PIN_1, 50)
                pwm_gate2 = GPIO.PWM(GATE_PIN_2, 50)
                pwm_gate3 = GPIO.PWM(GATE_PIN_3, 50)
                pwm_gate4 = GPIO.PWM(GATE_PIN_4, 50)

                # Start all PWM
                for pwm in [pwm_recycle1, pwm_recycle2, pwm_landfill1, pwm_landfill2,
                            pwm_gate1, pwm_gate2, pwm_gate3, pwm_gate4]:
                    pwm.start(0)

                # Initialize positions
                print("Setting initial positions...")
                set_servo_pair(pwm_recycle1, pwm_recycle2, SERVO_CLOSED_ANGLE_RECYCLE)
                set_servo_pair(pwm_landfill1, pwm_landfill2, SERVO_CLOSED_ANGLE_LAND)
                set_servo_pair(pwm_gate1, pwm_gate2, GATE_CLOSED_ANGLE_G1)
                set_servo_pair(pwm_gate3, pwm_gate4, GATE_CLOSED_ANGLE_G2)
                time.sleep(1)

                print("✓ All 8 servos initialized!")
                print(f"  Bins: GPIO {RECYCLABLE_SERVO_PIN_1},{RECYCLABLE_SERVO_PIN_2} (recycle: closed={SERVO_CLOSED_ANGLE_RECYCLE}°, open={SERVO_OPEN_ANGLE_RECYCLE}°)")
                print(f"        GPIO {LANDFILL_SERVO_PIN_1},{LANDFILL_SERVO_PIN_2} (landfill: closed={SERVO_CLOSED_ANGLE_LAND}°, open={SERVO_OPEN_ANGLE_LAND}°)")
                print(f"  Gates: GPIO {GATE_PIN_1},{GATE_PIN_2} (Gate 1: closed={GATE_CLOSED_ANGLE_G1}°, open={GATE_OPEN_ANGLE_G1}°)")
                print(f"         GPIO {GATE_PIN_3},{GATE_PIN_4} (Gate 2: closed={GATE_CLOSED_ANGLE_G2}°, open={GATE_OPEN_ANGLE_G2}°)")
            except Exception as e:
                print(f"❌ Failed to initialize servos: {e}")
                enable_servo = False
                if pwm_recycle1:
                    for pwm in [pwm_recycle1, pwm_recycle2, pwm_landfill1, pwm_landfill2,
                                pwm_gate1, pwm_gate2, pwm_gate3, pwm_gate4]:
                        if pwm:
                            pwm.stop()
                GPIO.cleanup()

    # Initialize camera
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
            print("✓ Picamera2 initialized")
        except Exception as e:
            print(f"⚠ Picamera2 failed: {e}")
            picam2 = None

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
            return

    print("\nCONTROLS: q=Quit | s=Screenshot | +/-=Confidence")
    if headless:
        print("Note: Running headless. Press Ctrl+C to stop.")
        import os
        os.makedirs('detections', exist_ok=True)
    print("=" * 70 + "\n")

    current_conf = conf_threshold
    frame_count = 0

    # State machine variables
    state = "WAITING_GATE1"
    last_state_change = time.time()
    last_detection_time = 0
    detected_waste_type = None

    try:
        while True:
            # Get frame
            if picam2 is not None:
                frame = picam2.capture_array()
                ret = True
            else:
                ret, frame = cap.read()

            if not ret or frame is None:
                print("Failed to grab frame")
                break

            frame_count += 1
            current_time = time.time()

            # Run detection
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
                    label = f"{waste_type} {confidence:.0%}"
                    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(frame, (x1, y1 - h - 8), (x1 + w + 4, y1), color, -1)
                    cv2.putText(frame, label, (x1 + 2, y1 - 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # State machine logic
            is_object_detected = (recyclable > 0) or (landfill > 0)

            if enable_servo and pwm_recycle1 is not None:

                if state == "WAITING_GATE1":
                    # Wait for detection to clear, then open Gate 1
                    if is_object_detected:
                        last_detection_time = current_time
                    else:
                        # No object detected, wait to ensure clear
                        if current_time - last_detection_time > CLEAR_WAIT_TIME:
                            print("🚪 Opening Gate 1 - ready for bottle")
                            set_servo_pair(pwm_gate1, pwm_gate2, GATE_OPEN_ANGLE_G1)
                            state = "GATE1_OPEN"
                            last_state_change = current_time

                elif state == "GATE1_OPEN":
                    # Gate 1 is open, wait for bottle to enter
                    if is_object_detected:
                        # Bottle detected! Close Gate 1 and classify
                        print("✓ Bottle detected! Closing Gate 1")
                        set_servo_pair(pwm_gate1, pwm_gate2, GATE_CLOSED_ANGLE_G1)
                        state = "CLASSIFYING"
                        last_state_change = current_time
                        detected_waste_type = None
                    elif current_time - last_state_change > 5.0:
                        # Gate been open too long with no bottle, close and wait
                        print("⚠️  Gate 1 timeout - no bottle detected, closing")
                        set_servo_pair(pwm_gate1, pwm_gate2, GATE_CLOSED_ANGLE_G1)
                        state = "IDLE_SLEEP"
                        last_state_change = current_time

                elif state == "CLASSIFYING":
                    # Classify the bottle and open appropriate bin
                    if recyclable > 0 and landfill == 0:
                        if detected_waste_type != "RECYCLABLE":
                            print("♻️  RECYCLABLE detected! Opening bin (GPIO 17, 5)")
                            set_servo_pair(pwm_recycle1, pwm_recycle2, SERVO_OPEN_ANGLE_RECYCLE)
                            set_servo_pair(pwm_landfill1, pwm_landfill2, SERVO_CLOSED_ANGLE_LAND)
                            detected_waste_type = "RECYCLABLE"
                            last_detection_time = current_time

                    elif landfill > 0 and recyclable == 0:
                        if detected_waste_type != "LANDFILL":
                            print("🗑️  LANDFILL detected! Opening bin (GPIO 18, 6)")
                            set_servo_pair(pwm_landfill1, pwm_landfill2, SERVO_OPEN_ANGLE_LAND)
                            set_servo_pair(pwm_recycle1, pwm_recycle2, SERVO_CLOSED_ANGLE_RECYCLE)
                            detected_waste_type = "LANDFILL"
                            last_detection_time = current_time

                    elif recyclable > 0 and landfill > 0:
                        if detected_waste_type != "BOTH":
                            print("⚠️  Both types detected! Opening BOTH bins (GPIO 17, 18)")
                            set_servo_pair(pwm_recycle1, pwm_recycle2, SERVO_OPEN_ANGLE_RECYCLE)
                            set_servo_pair(pwm_landfill1, pwm_landfill2, SERVO_OPEN_ANGLE_LAND)
                            detected_waste_type = "BOTH"
                            last_detection_time = current_time

                    # Wait for bin to stay open, then check if bottle is gone
                    if detected_waste_type is not None:
                        if current_time - last_detection_time > BIN_OPEN_DURATION:
                            if not is_object_detected:
                                # Bottle is gone, close bins and open Gate 2
                                print("✓ Bottle sorted! Closing bins, opening Gate 2")
                                set_servo_pair(pwm_recycle1, pwm_recycle2, SERVO_CLOSED_ANGLE_RECYCLE)
                                set_servo_pair(pwm_landfill1, pwm_landfill2, SERVO_CLOSED_ANGLE_LAND)
                                time.sleep(0.5)
                                set_servo_pair(pwm_gate3, pwm_gate4, GATE_OPEN_ANGLE_G2)
                                state = "GATE2_OPEN"
                                last_state_change = current_time
                            else:
                                # Still detecting, keep waiting
                                last_detection_time = current_time

                elif state == "GATE2_OPEN":
                    # Gate 2 is open, wait then close it
                    if current_time - last_state_change > GATE_OPEN_DURATION:
                        print("🚪 Closing Gate 2")
                        set_servo_pair(pwm_gate3, pwm_gate4, GATE_CLOSED_ANGLE_G2)
                        state = "WAITING_GATE1"
                        last_state_change = current_time
                        print("🔄 Ready for next bottle\n")

                elif state == "IDLE_SLEEP":
                    # Sleep when both gates open but nothing detected
                    if current_time - last_state_change > IDLE_SLEEP_TIME:
                        print("💤 Idle period complete, resuming...")
                        state = "WAITING_GATE1"
                        last_state_change = current_time

            # Stats overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (300, 200), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

            cv2.putText(frame, f"Recyclable: {recyclable}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Landfill: {landfill}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Unknown: {unknown}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"Conf: {current_conf:.2f}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"State: {state}", (10, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
            if detected_waste_type:
                cv2.putText(frame, f"Type: {detected_waste_type}", (10, 180),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Display or save
            if headless:
                if is_object_detected or (frame_count % 30 == 0):
                    filename = f'detections/frame_{frame_count:06d}.jpg'
                    cv2.imwrite(filename, frame)
                    if is_object_detected:
                        print(f"Frame {frame_count}: R={recyclable} L={landfill} - Saved")
            else:
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
        if enable_servo and pwm_recycle1 is not None:
            print("\nCleaning up servos...")
            set_servo_pair(pwm_recycle1, pwm_recycle2, SERVO_CLOSED_ANGLE_RECYCLE)
            set_servo_pair(pwm_landfill1, pwm_landfill2, SERVO_CLOSED_ANGLE_LAND)
            set_servo_pair(pwm_gate1, pwm_gate2, GATE_CLOSED_ANGLE_G1)
            set_servo_pair(pwm_gate3, pwm_gate4, GATE_CLOSED_ANGLE_G2)
            time.sleep(1)
            for pwm in [pwm_recycle1, pwm_recycle2, pwm_landfill1, pwm_landfill2,
                        pwm_gate1, pwm_gate2, pwm_gate3, pwm_gate4]:
                pwm.stop()
            GPIO.cleanup()
            print("✓ Servos cleaned up")

        if picam2 is not None:
            picam2.stop()
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("✓ Detection ended")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("RASPBERRY PI WASTE DETECTION - SEQUENTIAL GATE SYSTEM")
    print("=" * 70)

    while True:
        print("\n1. Run detection (with display)")
        print("2. Run detection (headless)")
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