# ♻️ Automated YOLOv11 Waste Sorter  

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-red?logo=raspberrypi)
![YOLOv11](https://img.shields.io/badge/YOLOv11-Detection-green?logo=ultralytics)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-success)

> **An autonomous dual-gate waste sorting system powered by YOLOv11, Raspberry Pi, and 8 precision servos.**  
> Designed to **identify and sort waste** into “Recyclable” or “Landfill” bins in real time.  

---

## 🧠 Overview  

The **Automated YOLOv11 Waste Sorter** combines **AI-based object detection**, **embedded hardware control**, and **mechanical automation**.  
A **custom YOLOv11 model** detects items through the Pi Camera, and a **Finite State Machine (FSM)** controls servo-driven gates and bins to sort waste automatically.  

This system ensures **continuous, one-by-one item processing** using two alternating gates for uninterrupted operation.  

---

## 🌟 Key Features  

### ⚡ Real-Time Classification  
- Detects and classifies waste instantly using a **custom-trained YOLOv11 model**.  
- Powered by **Ultralytics YOLOv11** and optimized for Raspberry Pi.  

### 🔀 Dual-Gate System  
- Two alternating gates (`Gate 1`, `Gate 2`) ensure **non-stop item flow**.  
- While one gate is closed and detecting, the other prepares for the next item.  

### ⚙️ Balanced 8-Servo Architecture  
| Component | Servos | Purpose |
|------------|---------|----------|
| ♻️ Recyclable Bin | 2 | Balanced lid lift |
| 🗑️ Landfill Bin | 2 | Balanced lid lift |
| 🚪 Gate 1 | 2 | Hold and release items |
| 🚪 Gate 2 | 2 | Hold and release items |

### 🧩 Robust Finite State Machine (FSM)  
| State | Description |
|--------|-------------|
| **CLOSED** | Detect & classify object |
| **WAITING_CLEAR** | Wait for object to leave view |
| **OPENING** | Open active gate for next item |
| **OPEN** | Hold open, close, and toggle gate |

### 🧱 Raspberry Pi Optimized  
- Uses `RPi.GPIO` for precise hardware control.  
- Uses `picamera2` for efficient image streaming.  
- Lightweight and fully compatible with **Raspberry Pi 4/5**.  

---

## 🛠️ Hardware Requirements  

| Component | Quantity | Description |
|------------|-----------|-------------|
| Raspberry Pi 5 | 1 | Main controller |
| Pi Camera Module | 1 | For image detection |
| SG90 Servo Motors | 8 | 4 for bins, 4 for gates |
| Ultrasonic Sensor HC-SR04 | 1 | Optional object sensing |
| Jumper Wires | — | GPIO connections |
| Wood, Formex, Cardboad | - | Prototype |

---

## 🔌 GPIO Pinout  

| Component | Servo | GPIO Pin |
|------------|--------|----------|
| ♻️ Recyclable Bin | Servo 1 | GPIO 17 |
|  | Servo 2 | GPIO 5 |
| 🗑️ Landfill Bin | Servo 1 | GPIO 18 |
|  | Servo 2 | GPIO 6 |
| 🚪 Gate 1 | Servo A | GPIO 19 |
|  | Servo B | GPIO 16 |
| 🚪 Gate 2 | Servo A | GPIO 22 |
|  | Servo B | GPIO 23 |

---

## 💾 Installation  

### 1️⃣ Clone Repository  
```bash
git clone https://github.com/Rie109/Hackathon.git
cd Hackathon
```

### 2️⃣ Install Dependencies  
```bash
pip install ultralytics opencv-python-headless RPi.GPIO picamera2
```

If `picamera2` fails to install:
```bash
sudo apt update
sudo apt install -y python3-picamera2
```

### 3️⃣ Add Your YOLOv11 Model  
Place your trained model file `best.pt` at:  
```
/home/harry/Hackathon/best.pt
```
Or modify this line in the script:
```python
MODEL_PATH = '/your/path/to/best.pt'
```

---

## 🚀 Run the System  

Execute the main script:  
```bash
python waste_sorter.py
```

You’ll see this startup menu:  
```
RASPBERRY PI WASTE DETECTION SYSTEM - BALANCED BIN VERSION
===========================================================

1. Run detection (with display)
2. Run detection (headless - no display)
3. Run detection + servo control (with display)
4. Run detection + servo control (headless)
0. Exit
```

💡 **Tip:**  
- Use **1 or 2** to test camera and detection accuracy.  
- Use **3 or 4** for full sorting system with all 8 servos.  

---

## ⚙️ Configuration  

Tweak angles and timings at the top of the script:  
```python
SERVO_CLOSED_ANGLE = 90
SERVO_OPEN_ANGLE   = 45
GATE_CLOSED_ANGLE  = 90
GATE_OPEN_ANGLE    = 45

bin_open_duration = 2.5  # seconds
clear_wait_time   = 1.0  # seconds
```

---

## ⚠️ Known Issues / Improvements  

- Current version uses `time.sleep()` in servo control, causing short **camera freeze** periods.  
- Next iteration: implement **non-blocking timers** for smoother detection.  
- Future goal: add **more waste categories** and **adaptive gate control** for improved accuracy.  

---

## 📸 Demo  

> *(Insert a GIF or image of the system in action here)*  

**Sample Output:**  
```
[INFO] Gate 1 - Object Detected: ♻️ Recyclable
[INFO] Opening Recyclable Bin...
[INFO] Item Sorted Successfully!
[INFO] Switching to Gate 2...
```

---

## 🤝 Contributors  

| Name | Role | Focus Area |
|------|------|-------------|
| **Harry Nguyen** | Developer | Camera Installation, YOLOv11 Integration |
| **Andrew Dang** | Developer | State Machine, Servo Installation |
| **Huy Le** | Designer | Prototype Design, Testing |
| **Jayden Dong** | Full-stack Developer | Waste-Tracking App Development |

---

## 📚 References

Bochkovskiy, A., Wang, C. Y., & Liao, H. Y. M. (2024). *Ultralytics YOLO11: Redefine what’s possible in AI* [Software]. Ultralytics. Retrieved from https://docs.ultralytics.com/models/yolo11/ :contentReference[oaicite:0]{index=0}

Dwyer, B., Nelson, J., Hansen, T., et al. (2025). *Roboflow (Version 1.0) [Software]*. Retrieved from https://roboflow.com/ :contentReference[oaicite:1]{index=1}

Bradski, G. (2000). “The OpenCV Library.” *Dr. Dobb’s Journal of Software Tools*. :contentReference[oaicite:2]{index=2}

Croston, B. (n.d.). RPi.GPIO: A Python module to control the GPIO on a Raspberry Pi [Software]. Retrieved from https://sourceforge.net/p/raspberry-gpio-python/wiki/Examples/ :contentReference[oaicite:3]{index=3}

Raspberry Pi Ltd. (n.d.). Picamera2: The libcamera-based Python interface for Raspberry Pi cameras [Software]. Retrieved from https://github.com/raspberrypi/picamera2 :contentReference[oaicite:4]{index=4}


