# 🖐️ AI Virtual Controller using Hand Gestures

> A real-time computer vision system for controlling mouse, keyboard, and volume using hand gestures.

A real-time, webcam-based virtual controller built with **Python, OpenCV, and MediaPipe**.
Control your mouse, scroll, adjust system volume, type on an on-screen keyboard, and
toggle the whole system on/off with a clap — no mouse or keyboard required.

![status](https://img.shields.io/badge/status-active-brightgreen) ![python](https://img.shields.io/badge/python-3.10-blue)

---

## ✨ Features

| Feature | How it works |
|---|---|
| 🖱️ Mouse movement | Point with your index finger — the cursor follows smoothly |
| 👆 Left click | Pinch thumb + index finger together |
| ✌️ Right click | Pinch thumb + middle finger together |
| 📜 Scrolling | Raise index + middle finger, move hand up/down |
| 🔊 Volume control | Spread thumb + pinky apart — distance maps to volume % |
| ⌨️ Virtual keyboard | Hover your fingertip over an on-screen key to "type" it |
| 👏 System toggle | Clap to activate/deactivate all tracking (or press `c`) |
| 🎨 Pastel UI overlay | Live landmarks, gesture labels, FPS, and status indicator |

---

## 📂 Project Structure

```
ai_virtual_controller/
│
├── main.py                # Entry point — runs the camera loop & UI
├── hand_tracker.py         # MediaPipe hand detection & landmark utilities
├── gesture_controller.py   # Mouse move / click / scroll actions
├── virtual_keyboard.py     # On-screen keyboard + dwell-time typing
├── volume_control.py       # System volume via pycaw (Windows)
├── clap_detector.py        # Microphone-based clap detection (background thread)
├── utils.py                # Shared colors, smoothing, FPS counter, helpers
├── requirements.txt        # Pinned dependencies
└── README.md                # You are here
```

Each file has a single, clear responsibility — this makes the project easy to
read, easy to extend, and easy to explain in an interview.

---

## ⚙️ Setup Instructions

### 1. Install Python 3.10

This project is built and tested against **Python 3.10**. MediaPipe's classic
`solutions` API (used here for simplicity and speed) only ships pre-built
binaries for Python 3.8–3.11 — on Python 3.12+ you'll hit
`AttributeError: module 'mediapipe' has no attribute 'solutions'`. If you
already have a newer Python installed, download 3.10 from
[python.org](https://www.python.org/downloads/) alongside it.

### 2. Create a virtual environment (recommended)

```bash
# Windows
py -3.10 -m venv venv
venv\Scripts\activate

# macOS / Linux
python3.10 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note on `pycaw`**: it's Windows-only (it wraps the Windows Core Audio API).
> On macOS/Linux, `requirements.txt` skips installing it automatically, and
> `volume_control.py` falls back to a "simulated" mode so the rest of the app
> still runs — the volume percentage is calculated but not applied to the OS.

### 4. Run the project

```bash
cd ai_virtual_controller
python main.py
```

A window titled **"AI Virtual Controller - Hand Gestures"** will open showing your
webcam feed with the pastel overlay UI. Grant camera/microphone permissions if
your OS prompts you.

---

## 🎮 Gesture & Keyboard Reference

| Gesture | Action |
|---|---|
| ☝️ Index finger only up | Move mouse |
| 🤏 Thumb + index pinch | Left click |
| 🤏 Thumb + middle pinch | Right click |
| ✌️ Index + middle up | Scroll (move hand vertically) |
| 🤙 Thumb + pinky up (others down) | Volume control |
| 🖖 Index + middle + ring up | Toggle Typing Mode |
| 👏 Clap | Toggle system Active / Inactive |

| Key | Action |
|---|---|
| `q` | Quit the application |
| `t` | Toggle Typing Mode on/off |
| `c` | Toggle system Active/Inactive (manual clap substitute) |
| `=` | Increase cursor sensitivity (snappier, more jitter) |
| `-` | Decrease cursor sensitivity (smoother, more lag) |

---

## 🚀 Performance Optimization Notes

This project is built to run smoothly on an average laptop, without a GPU:

1. **Lower capture resolution** — `CAM_WIDTH/CAM_HEIGHT` in `main.py` default to
   `960x540` instead of full HD. Lower resolution = far less pixel data for
   MediaPipe to process per frame.
2. **`max_hands=1`** — tracking two hands roughly doubles MediaPipe's per-frame cost.
   We only need one for this controller.
3. **Frame skipping** — set `PROCESS_EVERY_N_FRAMES = 2` in `main.py` to run hand
   detection on every other frame on slower machines.
4. **Skip tracking while inactive** — when the system is toggled off (via clap
   or `c`), hand detection is skipped entirely, dropping CPU usage close to idle.
5. **`pyautogui.PAUSE = 0`** — removes PyAutoGUI's default 0.1s delay after every
   call, which would otherwise cap you well under 10 actions/second.
6. **Exponential smoothing, not heavy filtering** — cursor jitter is reduced with
   a lightweight moving-average (`utils.Smoother`) instead of a costly Kalman filter.
7. **Background audio thread** — clap detection runs on its own thread via
   `sounddevice`, so microphone processing never blocks the video loop.

**Rule of thumb:** if FPS is low, lower `CAM_WIDTH`/`CAM_HEIGHT` first, then try
`PROCESS_EVERY_N_FRAMES = 2`, and make sure you're in a well-lit room (MediaPipe
works harder in low light).

---

## 🐞 Troubleshooting

**`AttributeError: module 'mediapipe' has no attribute 'solutions'`**
You're likely on Python 3.12+. Reinstall using Python 3.10 as described in Setup.

**Camera window doesn't open / `Could not access the webcam`**
- Make sure no other app (Zoom, Teams, another Python script) is using the camera.
- Try changing `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)` in `main.py` if you
  have multiple cameras.
- On macOS: grant camera access under *System Settings → Privacy & Security → Camera*.

**`ModuleNotFoundError: No module named 'cv2'` / `'mediapipe'` / etc.**
Your virtual environment isn't activated, or `pip install -r requirements.txt`
didn't complete. Re-run the install step inside the activated venv.

**Mouse doesn't move / `pyautogui` errors on Linux**
- PyAutoGUI needs a graphical (X11) session and `python3-tk`:
  `sudo apt-get install python3-tk python3-dev`
- On Wayland-only sessions, PyAutoGUI's mouse control may not work — switch to
  an X11 session if your distro offers one.

**Volume gesture doesn't change system volume**
`pycaw` is Windows-only. On macOS/Linux the app runs in simulated mode (see
Setup step 3). To wire up real control there, swap the `SetMasterVolumeLevel`
call in `volume_control.py` for `osascript` (Mac) or `pactl`/`amixer` (Linux).

**Clap detection doesn't trigger, or triggers randomly**
- Adjust the `threshold` value passed to `ClapDetector` in `main.py` — lower it
  if claps aren't detected, raise it if background noise triggers false positives.
- `PortAudio` errors: install PortAudio — `brew install portaudio` (Mac) or
  `sudo apt-get install libportaudio2` (Linux).
- You can always fall back to pressing `c` to toggle the system manually.

**Cursor is jittery or laggy**
Press `-` while the app is running to smooth it out (trades responsiveness for
stability), or `=` for a snappier, more direct feel.

---

## 🧠 Design Notes (why some choices were made)

- **PyAutoGUI for both mouse *and* keyboard**, instead of adding `pynput` as a
  second automation library — one dependency, one consistent API, fewer moving
  parts for a project of this scope. `pynput` is still listed in
  `requirements.txt` as a drop-in alternative if you'd like to extend the
  keyboard module with features PyAutoGUI doesn't support (e.g. key-hold events).
- **Dwell-time typing** instead of tap detection — detecting a physical "tap" in
  2D from a webcam is unreliable (depth is ambiguous). Hovering for a short,
  visually-animated moment is simple and far more accurate.
- **One hand only** — a deliberate performance/complexity trade-off; the full
  gesture set (mouse, clicks, scroll, volume, typing) doesn't need a second hand.

---

## 🌱 Possible Extensions

- Add a second hand for two-handed gestures (e.g. zoom via pinch-and-spread)
- Swap the dwell-time keyboard for a swipe-to-type gesture
- Replace the amplitude-threshold clap detector with a small trained audio
  classifier for more robust clap detection in noisy environments
- Package as a system tray app that starts/stops with a hotkey

---

## 📜 License

Free to use, modify, and extend for learning or portfolio purposes.
