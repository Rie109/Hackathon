# 🤖 Automated YOLOv8 Waste Sorter

An **autonomous waste-sorting system** powered by a **Raspberry Pi**, a **camera**, and a **custom-trained YOLOv8 model**.  
The system detects waste items and sorts them as **“Recyclable”** or **“Landfill”** using a **balanced 8-servo dual-gate mechanism** — enabling smooth, continuous, one-by-one sorting.

---

## 🌟 Key Features

- ⚡ **Real-Time Classification**  
  Detects and classifies waste instantly using YOLOv8.

- 🔀 **Dual-Gate System**  
  Two sequential gates alternate operation, enabling seamless continuous sorting.

- 🦾 **Balanced 8-Servo Design**
  - **4 Bin Servos** (2 per bin lid: Recyclable, Landfill)  
  - **4 Gate Servos** (2 per gate: Gate 1, Gate 2)

- 🧠 **Finite State Machine (FSM) Control**  
  A 4-state FSM governs the sorting process with precision and reliability.

- 🪶 **Optimized for Raspberry Pi**  
  Built with `RPi.GPIO` for hardware control and `picamera2` for efficient video streaming.

---

## ⚙️ System Workflow

The Finite State Machine (FSM) operates through **4 core states** to control sorting cycles:

### 🧩 1. CLOSED (Detect & Sort)
- Wait for object detection at active gate.  
- YOLOv8 classifies the item (`RECYCLABLE` or `LANDFILL`).  
- Opens the correct bin lid (via dual servos).  
- Waits 2.5 seconds for drop → then closes the lid.  
- Transitions to **WAITING_CLEAR**.

---

### 🕒 2. WAITING_CLEAR
- Waits until the object leaves the camera view.  
- When clear for 1 second → transitions to **OPENING**.

---

### 🚪 3. OPENING
- Opens the current gate (via dual servos) to release the next item.  
- Transitions immediately to **OPEN**.

---

### 🔄 4. OPEN (Toggle & Reset)
- Keeps gate open for 1 second.  
- Closes it and toggles to the other gate (Gate 1 ↔ Gate 2).  
- Returns to **CLOSED** — ready for the next cycle.

> 💡 This A-B-A-B alternation enables continuous, one-by-one sorting.

---

## 🧰 Hardware Requirements

| Component | Description |
|------------|--------------|
| 🧠 Raspberry Pi 5 | Main controller |
| 📷 Pi Camera Module | Object detection |
| 🔧 8 × SG90 Servos | 4 for bins + 4 for gates |
| 📡 Ultrasonic Sensor HC-SR04 | Object detection trigger |
| 🪵 Structure | Wood, Formex, or cardboard |
| 🔌 Jumper wires | For servo & sensor connections |
| 🧱 Custom chassis | 3D printed / laser-cut |

---

## 🧩 Wiring Diagram (GPIO)

| Component | GPIO Pins |
|------------|-----------|
| ♻️ Recyclable Bin Servos | GPIO 17, GPIO 5 |
| 🗑️ Landfill Bin Servos | GPIO 17, GPIO 5 |
| 🚪 Gate A Servos | GPIO 19, GPIO 16 |
| 🚪 Gate B Servos | GPIO 22, GPIO 23 |

---

## 💻 Software Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Rie109/Hackathon.git
cd Hackathon
