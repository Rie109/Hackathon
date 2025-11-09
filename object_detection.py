from ultralytics import YOLO
import cv2
from pathlib import Path
import yaml
import time
import numpy as np

# Try to import picamera2 for Raspberry Pi camera support
try:
    from picamera2 import Picamera2

    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("⚠ Warning: picamera2 not available, will try standard cv2")

# Try to import GPIO for servo control
try:
    from gpiozero import Servo, Button
    from time import sleep

    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠ Warning: gpiozero not available, servo control disabled")

# GPIO Pin Configuration
RECYCLABLE_SERVO_PIN = 17
LANDFILL_SERVO_PIN = 18
GATE_SERVO_1 = 19
GATE_SERVO_2 = 20
GATE_SERVO_3 = 21
GATE_SERVO_4 = 22
START_BUTTON_PIN = 26


# YOUR PATH - Updated for Raspberry Pi
PROJECT_PATH = Path('D:/Myself/University/EE/TrashCan')

# Categories
RECYCLABLE_ITEMS = ['bottle-glass', 'bottle-plastic', 'tin can', 'gym bottle']
LANDFILL_ITEMS = ['cup-disposable', 'glass-wine', 'glass-normal', 'glass-mug', 'cup-handle']
HUMAN_CLASSES = ['Human', 'person', 'human', 'people', 'man', 'woman']


def classify_waste_type(class_name):
    """Classify detected object"""
    class_lower = class_name.lower()
    if class_lower in [h.lower() for h in HUMAN_CLASSES]:
        return "PERSON", (255, 0, 255)
    elif class_lower in [item.lower() for item in RECYCLABLE_ITEMS]:
        return "RECYCLABLE", (0, 255, 0)
    elif class_lower in [item.lower() for item in LANDFILL_ITEMS]:
        return "LANDFILL", (0, 0, 255)
    else:
        return "UNKNOWN", (255, 255, 0)


def analyze_dataset():
    """Quick dataset analysis"""
    yaml_path = PROJECT_PATH / 'data.yaml'
    if not yaml_path.exists():
        print("❌ data.yaml not found!")
        return None

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    base_path = Path(data['path'])
    train_path = base_path / data.get('train', 'train/images')

    if train_path.exists():
        images = list(train_path.glob('*.jpg')) + list(train_path.glob('*.png'))
        return len(images)
    return 0


def train_ultra_fast():
    """Ultra-fast training - 5 epochs for quick testing"""
    print("\n🚀 ULTRA FAST MODE (5 epochs)")
    print("=" * 70)

    model = YOLO('yolo11n.pt')  # Nano model
    yaml_path = PROJECT_PATH / 'data.yaml'

    print("Starting ultra-fast training...")
    print("Estimated time: 3-8 minutes\n")

    results = model.train(
        data=str(yaml_path),
        epochs=5,
        batch=16,
        imgsz=416,
        device=0,
        workers=8,
        cache='ram',
        patience=3,
        amp=True,
        verbose=True,
        plots=True,
    )

    print("\n✓ Ultra-fast training complete!")


def train_quick_test():
    """Quick test - 10-20 epochs for validation"""
    print("\n⚡ QUICK TEST MODE (20 epochs)")
    print("=" * 70)

    num_images = analyze_dataset()
    print(f"Dataset size: {num_images} images\n")

    model = YOLO('yolo11n.pt')  # Nano model
    yaml_path = PROJECT_PATH / 'data.yaml'

    print("Starting quick test training...")
    print("Estimated time: 10-20 minutes\n")

    results = model.train(
        data=str(yaml_path),
        epochs=20,
        batch=16,
        imgsz=640,
        device=0,
        workers=8,
        cache='disk',
        patience=5,
        amp=True,
        verbose=True,
        plots=True,
        fraction=0.7,  # Use 70% of data
    )

    print("\n✓ Quick test complete!")


def train_balanced():
    """Balanced training - good speed and accuracy"""
    print("\n⚙️ BALANCED MODE (50 epochs, Small model)")
    print("=" * 70)

    num_images = analyze_dataset()
    print(f"Dataset size: {num_images} images\n")

    model = YOLO('yolo11n.pt')  # Small model
    yaml_path = PROJECT_PATH / 'data.yaml'

    print("Starting balanced training...")
    print("Estimated time: 1-2 hours\n")

    input("Press ENTER to start...")

    results = model.train(
        data=str(yaml_path),
        epochs=50,
        batch=16,
        imgsz=640,
        device=0,
        workers=8,
        cache='disk',
        patience=10,
        amp=True,
        verbose=True,
        plots=True,
    )

    print("\n✓ Balanced training complete!")


def train_full_quality():
    """Full quality training - best results"""
    print("\n🎯 FULL QUALITY MODE (100 epochs, Small model)")
    print("=" * 70)

    num_images = analyze_dataset()
    print(f"Dataset size: {num_images} images\n")

    model = YOLO('yolo11s.pt')  # Small model
    yaml_path = PROJECT_PATH / 'data.yaml'

    print("Starting full quality training...")
    print("Estimated time: 2-4 hours\n")

    input("Press ENTER to start...")

    results = model.train(
        data=str(yaml_path),
        epochs=100,
        batch=16,
        imgsz=640,
        device=0,
        workers=8,
        cache='disk',
        patience=15,
        amp=True,
        verbose=True,
        plots=True,

        # Enhanced augmentation
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
    )

    print("\n✓ Full quality training complete!")


def train_overnight():
    """Overnight training - maximum accuracy"""
    print("\n🌙 OVERNIGHT MODE (150 epochs, Medium model)")
    print("=" * 70)

    num_images = analyze_dataset()
    print(f"Dataset size: {num_images} images\n")

    model = YOLO('yolo11m.pt')  # Medium model
    yaml_path = PROJECT_PATH / 'data.yaml'

    print("Starting overnight training...")
    print("Estimated time: 4-8 hours\n")
    print("⚠️ This will run for several hours!")

    confirm = input("Type 'yes' to confirm: ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return

    results = model.train(
        data=str(yaml_path),
        epochs=150,
        batch=16,
        imgsz=640,
        device=0,
        workers=8,
        cache='disk',
        patience=20,
        amp=True,
        verbose=True,
        plots=True,

        # Full augmentation
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=15.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
    )

    print("\n✓ Overnight training complete!")


def train_custom():
    """Custom training with your own parameters"""
    print("\n🔧 CUSTOM TRAINING MODE")
    print("=" * 70)

    num_images = analyze_dataset()
    print(f"Dataset size: {num_images} images\n")

    # Get parameters
    print("Model size:")
    print("  n = Nano (fastest)")
    print("  s = Small (recommended)")
    print("  m = Medium (most accurate)")
    model_choice = input("Choose (n/s/m) [s]: ").strip().lower() or 's'
    model_files = {'n': 'yolo11n.pt', 's': 'yolo11s.pt', 'm': 'yolo11m.pt'}

    epochs = int(input("Epochs [50]: ").strip() or "50")
    batch = int(input("Batch size [16]: ").strip() or "16")
    imgsz = int(input("Image size [640]: ").strip() or "640")

    model = YOLO(model_files[model_choice])
    yaml_path = PROJECT_PATH / 'data.yaml'

    print(f"\nStarting custom training...")
    print(f"Model: {model_files[model_choice]}, Epochs: {epochs}, Batch: {batch}, Size: {imgsz}\n")

    input("Press ENTER to start...")

    results = model.train(
        data=str(yaml_path),
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=0,
        workers=8,
        cache='disk',
        patience=15,
        amp=True,
        verbose=True,
        plots=True,
    )

    print("\n✓ Custom training complete!")


def run_webcam_detection(conf_threshold=0.25, headless=False, enable_servo=False):
    """Run webcam detection with trained model"""
    print("\n📹 WEBCAM DETECTION")
    if headless:
        print("(HEADLESS MODE - Saving frames to disk)")
    if enable_servo:
        print("(SERVO MODE - Enabled)")
    print("=" * 70)

    # Use direct path to best.pt
    model_path = Path('/home/harry/TrashCan/best.pt')

    if not model_path.exists():
        print(f"❌ Model not found at {model_path}")
        print("\nPlease transfer your trained model:")
        print("  scp runs/detect/trainXX/weights/best.pt harry@192.168.137.20:~/TrashCan/best.pt")
        return

    print(f"✓ Using: {model_path}\n")

    model = YOLO(str(model_path))
    print(f"✓ Classes: {', '.join(model.names.values())}")

    # Initialize servos if enabled
    servo_recycle = None
    servo_landfill = None
    start_button = None

    if enable_servo:
        if not GPIO_AVAILABLE:
            print("❌ GPIO not available. Servo control disabled.")
            print("Install: sudo apt-get install python3-gpiozero")
            enable_servo = False
        else:
            try:
                print("Initializing servos...")
                servo_recycle = Servo(RECYCLABLE_SERVO_PIN)
                servo_landfill = Servo(LANDFILL_SERVO_PIN)
                gate_servo_1 = Servo(GATE_SERVO_1)
                gate_servo_2 = Servo(GATE_SERVO_2)
                gate_servo_3 = Servo(GATE_SERVO_3)
                gate_servo_4 = Servo(GATE_SERVO_4)
                start_button = Button(START_BUTTON_PIN)

                # Initialize servo positions (both at neutral/closed position)
                servo_recycle.mid()  # 0 degrees (closed)
                servo_landfill.mid()  # 0 degrees (closed)
                gate_servo_1.mid()
                gate_servo_2.mid()
                gate_servo_3.mid()
                gate_servo_4.mid()
                sleep(1)
                
                print("✓ Servos initialized")
                print(f"  Recyclable servo: GPIO {RECYCLABLE_SERVO_PIN} (turns right when recyclable detected)")
                print(f"  Landfill servo: GPIO {LANDFILL_SERVO_PIN} (turns left when landfill detected)")
                print(f"  Start button: GPIO {START_BUTTON_PIN}")
                print("All gates are set up at their initial position")
            except Exception as e:
                print(f"❌ Failed to initialize servos: {e}")
                enable_servo = False
                servo_recycle = None
                servo_landfill = None
                gate_servo_1 = None
                gate_servo_2 = None
                gate_servo_3 = None
                gate_servo_4 = None
                start_button = None
            
            #initialize curren state at IDLE
            current_state = 0

    # Initialize camera - Try Picamera2 first (for Arducam/libcamera), then fall back to cv2
    picam2 = None
    cap = None

    if PICAMERA2_AVAILABLE:
        try:
            print("Initializing Picamera2...")
            picam2 = Picamera2()

            # Configure camera for RGB888 format (compatible with OpenCV)
            config = picam2.create_preview_configuration(
                main={"size": (1280, 720), "format": "RGB888"}
            )
            picam2.configure(config)
            picam2.start()

            # Give camera time to initialize
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
            print("❌ Could not open camera with any method")
            print("\nTroubleshooting:")
            print("  1. Check camera connection")
            print("  2. Run: libcamera-hello --list-cameras")
            print("  3. Install picamera2: sudo apt-get install python3-picamera2")
            return

    print("\nCONTROLS: q=Quit | s=Screenshot | +/-=Confidence")
    if headless:
        print("Note: Running in headless mode. Press Ctrl+C to stop.")
        print("Frames will be saved to: ~/TrashCan/detections/")
        import os
        os.makedirs('detections', exist_ok=True)
    print("=" * 70 + "\n")

    current_conf = conf_threshold
    frame_count = 0
    save_interval = 30 if headless else 0  # Save every 30 frames in headless mode

    # Servo control variables
    last_detection_time = 0
    detection_cooldown = 3  # seconds between servo activations
    servo_active = False

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

            recyclable = landfill = person = unknown = 0
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
                    elif waste_type == "PERSON":
                        person += 1
                    else:
                        unknown += 1

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    label = f"{class_name} {confidence:.0%}"

                    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    cv2.rectangle(frame, (x1, y1 - h - 8), (x1 + w + 4, y1), color, -1)
                    cv2.putText(frame, label, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Servo control logic

            is_object_detected = (recyclable > 0) or (landfill > 0)
            if enable_servo:
                #state 0: wait for the button
                if current_state == 0:
                    if start_button.is_pressed:
                        current_state = 1
                elif current_state == 1:
                    #drop 1 object for the first time:
                    gate_servo_1.min()
                    gate_servo_2.min()
                    gate_servo_3.min()
                    gate_servo_4.min()
                
                    sleep(1)
                    #turn the gate
                    gate_servo_1.mid()
                    gate_servo_2.mid()
                    gate_servo_3.mid()
                    gate_servo_4.mid()
                    current_state == 2
                elif current_state == 2:
                    if is_object_detected:
                        current_state = 3
                elif current_state == 3:
                    if recyclable > 0 and landfill == 0: #detect recyclable
                        servo_recycle.max() #rotate recycle servo 90
                        servo_landfill.min() #keep the landfill servo at 0
                        sleep(2)  #wait for object to fall
                        servo_recycle.min()  #close the recycle servo
                    elif recyclable == 0 and landfill > 0: #detect landfill
                        servo_recycle.min() #keep the recycle servo at 0
                        servo_landfill.max() #rotate the landfill servo 90
                        sleep(2)  #wait for object to fall
                        servo_landfill.min()  #close the landfill servo
                    elif recyclable == 0 and landfill == 0: #detect human
                        servo_recycle.min() #keep the recycle servo at 0
                        servo_landfill.min() #keep the landfill servo at 0
                    current_state = 4  #turn to state 4
                elif current_state == 4:
                    if recyclable == 0 and landfill == 0:
                        current_state = 1
                




         '''   current_time = time.time()
            if enable_servo and servo_recycle is not None:
                # Check if enough time has passed since last detection
                if current_time - last_detection_time > detection_cooldown:
                    if recyclable > 0 and landfill == 0:
                        # Recyclable detected - turn right (max position)
                        print(f"♻️  RECYCLABLE detected! Servo turning RIGHT")
                        servo_recycle.max()  # Turn right (90 degrees)
                        servo_landfill.mid()  # Keep landfill closed
                        sleep(2)  # Wait for item to fall
                        servo_recycle.mid()  # Return to neutral
                        last_detection_time = current_time

                    elif landfill > 0 and recyclable == 0:
                        # Landfill detected - turn left (min position)
                        print(f"🗑️  LANDFILL detected! Servo turning LEFT")
                        servo_landfill.min()  # Turn left (-90 degrees)
                        servo_recycle.mid()  # Keep recyclable closed
                        sleep(2)  # Wait for item to fall
                        servo_landfill.mid()  # Return to neutral
                        last_detection_time = current_time

                    elif recyclable > 0 and landfill > 0:
                        # Both detected - don't activate servos
                        print("⚠️  Both recyclable and landfill detected - no action")
                        servo_recycle.mid()
                        servo_landfill.mid() '''

            # Stats overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (280, 170), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

            cv2.putText(frame, f"Recyclable: {recyclable}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Landfill: {landfill}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"People: {person}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
            cv2.putText(frame, f"Unknown: {unknown}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"Conf: {current_conf:.2f}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255),
                        2)

            # Headless mode: save frames periodically or when objects detected
            if headless:
                total_detections = recyclable + landfill + person
                if total_detections > 0 or (frame_count % save_interval == 0):
                    filename = f'detections/frame_{frame_count:06d}.jpg'
                    cv2.imwrite(filename, frame)
                    if total_detections > 0:
                        print(f"Frame {frame_count}: R={recyclable} L={landfill} P={person} - Saved to {filename}")
                    elif frame_count % (save_interval * 10) == 0:
                        print(f"Frame {frame_count}: Running... (last save: {filename})")
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

    finally:
        # Cleanup
        if enable_servo and servo_recycle is not None:
            print("\nCleaning up servos...")
            servo_recycle.mid()
            servo_landfill.mid()
            sleep(1)
            servo_recycle.detach()
            servo_landfill.detach()
            print("✓ Servos detached")

        if picam2 is not None:
            picam2.stop()
            print("Picamera2 stopped")
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("Detection ended")


def show_training_comparison():
    """Show comparison of all training modes"""
    print("\n" + "=" * 70)
    print("TRAINING MODE COMPARISON")
    print("=" * 70)

    num_images = analyze_dataset()
    if num_images:
        print(f"\nYour dataset: {num_images} training images")

    print("\n┌─────────────────┬────────┬──────┬─────────┬──────────────┬─────────────┐")
    print("│ Mode            │ Epochs │ Model│ Img Size│ Time Est.    │ Use Case    │")
    print("├─────────────────┼────────┼──────┼─────────┼──────────────┼─────────────┤")
    print("│ Ultra Fast      │   5    │ Nano │   416   │  3-8 min     │ Quick test  │")
    print("│ Quick Test      │   20   │ Nano │   640   │  10-20 min   │ Validation  │")
    print("│ Balanced        │   50   │ Small│   640   │  1-2 hours   │ Good results│")
    print("│ Full Quality    │  100   │ Small│   640   │  2-4 hours   │ Best results│")
    print("│ Overnight       │  150   │ Medium│  640   │  4-8 hours   │ Max accuracy│")
    print("│ Custom          │   ?    │  ?   │    ?    │  Varies      │ Your choice │")
    print("└─────────────────┴────────┴──────┴─────────┴──────────────┴─────────────┘")

    print("\n💡 Recommendations:")
    print("  • First time? Start with 'Ultra Fast' to test everything works")
    print("  • Need quick results? Use 'Quick Test' or 'Balanced'")
    print("  • Want best accuracy? Use 'Full Quality' or 'Overnight'")
    print("  • Have specific needs? Use 'Custom'")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("YOLO WASTE DETECTION - TRAINING OPTIONS")
    print("=" * 70)

    while True:
        print("\n1. Show training comparison")
        print("2. Ultra Fast (5 epochs, ~5 min)")
        print("3. Quick Test (20 epochs, ~15 min)")
        print("4. Balanced (50 epochs, ~1.5 hrs)")
        print("5. Full Quality (100 epochs, ~3 hrs)")
        print("6. Overnight (150 epochs, ~6 hrs)")
        print("7. Custom parameters")
        print("8. Run webcam detection (with display)")
        print("9. Run webcam detection (headless - no display)")
        print("10. Run webcam + servo (with display)")
        print("11. Run webcam + servo (headless)")
        print("0. Exit")

        choice = input("\nChoice (0-11): ").strip()

        try:
            if choice == '1':
                show_training_comparison()
            elif choice == '2':
                train_ultra_fast()
            elif choice == '3':
                train_quick_test()
            elif choice == '4':
                train_balanced()
            elif choice == '5':
                train_full_quality()
            elif choice == '6':
                train_overnight()
            elif choice == '7':
                train_custom()
            elif choice == '8':
                run_webcam_detection(headless=False)
            elif choice == '9':
                run_webcam_detection(headless=True)
            elif choice == '10': 
                run_webcam_detection(headless=False, enable_servo=True)
            elif choice == '11':
                run_webcam_detection(headless=True, enable_servo=True)
            elif choice == '0':
                print("\nExiting...")
                break
            else:
                print("Invalid choice!")
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")

        if choice not in ['1', '0']:
            input("\nPress ENTER to continue...")