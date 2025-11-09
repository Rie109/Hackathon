Automated YOLOv8 Waste Sorter

An autonomous waste-sorting system that uses a Raspberry Pi, a camera, and a custom-trained YOLOv8 model. The system identifies items as "Recyclable" or "Landfill" and employs a sophisticated 8-servo mechanism to sort them into the correct bin.   

🌟 Key Features
Real-Time Classification: Utilizes a YOLOv8 model to detect and classify waste items instantly.

Dual-Gate System: Employs two sequential sorting gates (Gate 1, Gate 2) that alternate, allowing for continuous, one-by-one item processing.

Balanced 8-Servo Design:

4 Bin Servos: Uses two servos per bin lid (Recyclable, Landfill) for a balanced and powerful lift.

4 Gate Servos: Uses two servos per gate (Gate 1, Gate 2) to reliably hold and release items.

Robust State Machine: The entire sorting process is managed by a 4-state Finite State Machine (FSM) for reliable, step-by-step operation.

Optimized for Raspberry Pi: Built natively with RPi.GPIO for direct hardware control and picamera2 for efficient camera streaming.

🤖 How It Works
The system operates on a 4-state Finite State Machine (FSM) that alternates between the two sorting gates.

State: CLOSED (Detect & Sort)

The system waits at the current active gate (e.g., Gate 1), which is closed, holding an item in view of the camera.

Once an item is detected (is_object_detected), YOLOv8 classifies it (e.g., "RECYCLABLE").

The corresponding bin (Recyclable or Landfill) opens using both its servos.

The system pauses for bin_open_duration (2.5 seconds) to allow the item to fall.

The bin closes.

The state transitions to WAITING_CLEAR.

State: WAITING_CLEAR

The system now waits for the object to disappear from the camera's view.

Once the object is gone (is_object_detected = False) for more than clear_wait_time (1 second), the system confirms the item is successfully sorted.

The state transitions to OPENING.

State: OPENING

The system opens the current gate (e.g., Gate 1) using both its servos.

This allows the next item in the queue to pass through and slide down to the other gate (Gate 2).

The state immediately transitions to OPEN.

State: OPEN (Toggle & Reset)

The system holds the gate open for 1 second.

It then closes the gate (Gate 1).

It "toggles" the active gate (current_gate flips from 1 to 2).

The FSM returns to the CLOSED state, now ready to repeat the entire process for the item waiting at Gate 2.

This A-B-A-B alternating cycle allows for continuous, one-by-one sorting.

🛠️ Hardware Requirements
Raspberry Pi 5

Camera (Raspberry Pi Camera Module)

8 x Servos SG90

Project chassis (3D printed, laser-cut, etc.)

Jumper wires

Ultrasonic Sensor HC-SRO4

Wood, Formex and cardboard paper

🔌 Wiring Diagram (GPIO)

Recyclable servo: GPIO Pin 17 and GPIO Pin 5

Landfill servo: GPIO Pin 17 and GPIO Pin 5

Gate A servo: GPIO Pin 19, GPIO Pin 16

Gate B servo: GPIO Pin 22, GPIO Pin 23

💾 Software Setup
1. Clone the Repository (if applicable):


git clone https://github.com/Rie109/Hackathon.git
cd Hackathon


2. Install Dependencies:

pip install ultralytics
pip install opencv-python-headless
pip install RPi.GPIO
pip install picamera2

Note: On some Raspberry Pi OS versions, picamera2 must be installed via apt.


sudo apt update
sudo apt install -y python3-picamera2

3. Download Model:

Obtain your trained best.pt YOLOv8 model.

Place it in the correct path as defined in the script: /home/harry/Hackathon/best.pt.

Alternatively, update the MODEL_PATH variable in the Python script to point to your model's location.

🚀 How to Run

Execute the main script from your terminal:


python your_script_name.py
You will see a menu to select the operating mode:

RASPBERRY PI WASTE DETECTION SYSTEM - BALANCED BIN VERSION
============================================================

1. Run detection (with display)
2. Run detection (headless - no display)
3. Run detection + servo control (with display)
4. Run detection + servo control (headless)
0. Exit

Choice (0-4):
Option 1 or 2: Use these to test the camera and YOLOv8 model accuracy without activating the servos.

Option 3 or 4: Use these to run the full sorting system with all 8 servos enabled.

🔧 Configuration & Known Issues
Configuration
You can fine-tune the servo behavior by adjusting these global variables at the top of the script:

SERVO_CLOSED_ANGLE = 90

SERVO_OPEN_ANGLE = 45

GATE_CLOSED_ANGLE = 90

GATE_OPEN_ANGLE = 45

⚠️ Known Issues / Limitations
The current implementation uses time.sleep() in two places:

Inside the set_servo_angle function (0.5s pause).

Inside the CLOSED state logic (2.5s pause).

This blocks the main thread, which will cause the camera feed to freeze during these periods. A future improvement would be to remove all time.sleep() calls from the loop and integrate them into the Finite State Machine using timer variables (like last_state_change), creating a fully non-blocking system.


