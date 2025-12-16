# 🚉 Parknam Railway Station Control Simulation (Lab Project)

This project is a **railway station control system simulation** developed as part of a **laboratory course**.
The system simulates basic railway interlocking concepts such as train arrival, platform assignment,
route locking, departure control, and emergency stop operations.

The simulation is implemented in **Python** using **Tkinter** for graphical visualization and user interaction.

---

## 🎯 Objectives

- To simulate train movement in a railway station environment
- To demonstrate basic interlocking and route control logic
- To visualize train operations using a GUI
- To practice event-driven programming with Python and Tkinter

---

## 🚆 System Features

- 🚄 Train arrival and departure simulation
- 🛤️ Two-platform station control (Platform 1 and Platform 2)
- 🔐 Route locking for inbound and outbound operations
- 🚦 Railway signal visualization (Home, Platform, and Starter signals)
- ⚠️ Emergency stop system with automatic reset
- 🖥️ Real-time graphical simulation using Tkinter
- 📝 Operation log with timestamps

---

## 🛠️ Technologies Used

- **Programming Language:** Python 3
- **GUI Framework:** Tkinter
- **Core Concepts:**
  - Object-Oriented Programming (OOP)
  - Event-driven programming
  - Simulation systems
  - Basic railway interlocking logic

---

## ⚙️ System Overview

1. The controller sets an inbound route to a selected platform
2. A train is called into the station
3. The system locks the route and simulates train movement
4. The train stops at the assigned platform
5. An outbound route is set to allow the train to depart
6. The train leaves the station and the system resets to ready state
7. Emergency stop can be triggered at any time to halt operations

---

## 🚀 How to Run

### Requirements
- Python 3 installed on your system

### Run the Simulation

```bash
python ParknamStation.py


## Project Structure
├── ParknamStation.py   # Main simulation and GUI logic
├── README.md           # Project documentation
└── .gitignore          # Git ignore configuration

## Author
Name: Supakit Japun
Major: Computer Engineering of Rajamangala University of Technology Thanyaburi
Course: Software Laboratory Course

## License
This project is developed for educational purposes only.
