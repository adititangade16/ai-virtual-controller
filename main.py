import time
import cv2

from hand_tracker import HandTracker
from gesture_controller import GestureController
from virtual_keyboard import VirtualKeyboard
from volume_control import VolumeController
from clap_detector import ClapDetector
from utils import (
    FPSCounter,
    COLOR_PRIMARY, COLOR_ACTIVE, COLOR_INACTIVE,
    COLOR_TEXT_DARK, COLOR_BG_PANEL, COLOR_ACCENT,
)

# 🔥 UPDATED CAMERA SIZE (IMPORTANT)
CAM_WIDTH, CAM_HEIGHT = 1280, 720

FRAME_REDUCTION = 100
PROCESS_EVERY_N_FRAMES = 1
CLICK_PINCH_THRESHOLD = 35
MODE_SWITCH_COOLDOWN = 1.0


class AppState:
    def __init__(self):
        self.system_active = True


def main():
    state = AppState()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

    # 🔥 WINDOW FIX (prevents cropping)
    cv2.namedWindow("AI Virtual Controller", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("AI Virtual Controller", CAM_WIDTH, CAM_HEIGHT)

    tracker = HandTracker(max_hands=1)
    gestures = GestureController(CAM_WIDTH, CAM_HEIGHT, frame_reduction=FRAME_REDUCTION)

    # 🔥 IMPORTANT: keyboard now uses full width
    keyboard = VirtualKeyboard(CAM_WIDTH, CAM_HEIGHT)

    volume = VolumeController()
    fps_counter = FPSCounter()

    def toggle_system():
        state.system_active = not state.system_active
        print(f"[System] {'ACTIVATED' if state.system_active else 'DEACTIVATED'}")

    clap = ClapDetector(on_clap_callback=toggle_system)
    clap.start()

    typing_mode = False
    last_mode_switch = 0.0
    frame_count = 0

    # ✅ HELP FEATURE (Guidelines at start)
    show_help = True
    help_start_time = time.time()
    HELP_DURATION = 8

    print("AI Virtual Controller running.")
    print("Press 'q' to quit | 't' to toggle typing mode | 'c' to toggle system")

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)

        # 🔥 FORCE FULL RESOLUTION (fix zoom/cut)
        frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))

        frame_count += 1
        process_this_frame = (frame_count % PROCESS_EVERY_N_FRAMES == 0)

        gesture_label = "Idle"
        landmark_list = []

        if state.system_active and process_this_frame:
            frame = tracker.find_hands(frame, draw=True)
            landmark_list = tracker.find_positions(frame)

        if state.system_active and landmark_list:
            fingers = tracker.fingers_up(landmark_list)
            index_tip = landmark_list[8][1:]

            now = time.time()

            if typing_mode:
                keyboard.draw(frame)  # 🔥 FULL KEYBOARD DRAW
                keyboard.update(frame, tuple(index_tip))
                gesture_label = "Typing"

            else:
                if fingers == [True, False, False, False, True]:
                    dist, _ = tracker.find_distance(landmark_list[4], landmark_list[20], frame, draw=True)
                    volume.set_volume_from_distance(dist)
                    gesture_label = "Volume"
                    gestures.reset_scroll()

                elif fingers == [False, True, True, False, False]:
                    gestures.scroll(index_tip[1])
                    gesture_label = "Scrolling"

                elif fingers[1] and not fingers[2]:
                    gestures.reset_scroll()
                    gestures.move_mouse(index_tip)
                    gesture_label = "Moving"

                    pinch_dist, _ = tracker.find_distance(landmark_list[4], landmark_list[8], frame, draw=True)
                    if pinch_dist < CLICK_PINCH_THRESHOLD:
                        if gestures.left_click():
                            gesture_label = "Left Click"
                    else:
                        right_pinch_dist, _ = tracker.find_distance(landmark_list[4], landmark_list[12])
                        if right_pinch_dist < CLICK_PINCH_THRESHOLD:
                            if gestures.right_click():
                                gesture_label = "Right Click"
                else:
                    gestures.reset_scroll()

                # 🔥 ENTER TYPING MODE
                if fingers == [False, True, True, True, False] and (now - last_mode_switch) > MODE_SWITCH_COOLDOWN:
                    typing_mode = True
                    last_mode_switch = now

            if time.time() < gestures.click_flash_until:
                cv2.circle(frame, tuple(index_tip), 25, COLOR_ACCENT, 4)

        elif state.system_active and typing_mode:
            keyboard.draw(frame)

        fps = fps_counter.update()

        draw_ui(frame, fps, gesture_label, state.system_active, typing_mode,
                keyboard.typed_text, gestures.smoother.smoothing_factor)

        # ✅ SHOW HELP (Guidelines UI)
        if show_help and (time.time() - help_start_time < HELP_DURATION):
            draw_help_overlay(frame)

        cv2.imshow("AI Virtual Controller", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('t'):
            typing_mode = not typing_mode
        elif key == ord('c'):
            toggle_system()
        elif key == ord('h'):
            show_help = not show_help
        elif key == ord('='):
            gestures.smoother.smoothing_factor = min(1.0, gestures.smoother.smoothing_factor + 0.05)
        elif key == ord('-'):
            gestures.smoother.smoothing_factor = max(0.05, gestures.smoother.smoothing_factor - 0.05)

    clap.stop()
    tracker.close()
    cap.release()
    cv2.destroyAllWindows()


def draw_ui(frame, fps, gesture_label, active, typing_mode, typed_text, sensitivity):
    h, w, _ = frame.shape

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 60), COLOR_BG_PANEL, cv2.FILLED)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    status_color = COLOR_ACTIVE if active else COLOR_INACTIVE
    status_text = "ACTIVE" if active else "INACTIVE"

    cv2.circle(frame, (25, 30), 10, status_color, cv2.FILLED)
    cv2.putText(frame, status_text, (45, 37),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_TEXT_DARK, 2)

    cv2.putText(frame, f"FPS: {int(fps)}", (w - 120, 37),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_TEXT_DARK, 2)

    text_size = cv2.getTextSize(gesture_label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
    cx = (w - text_size[0]) // 2
    cv2.putText(frame, gesture_label, (cx, 37),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_PRIMARY, 2)


def draw_help_overlay(frame):
    h, w, _ = frame.shape

    overlay = frame.copy()
    cv2.rectangle(overlay, (50, 50), (w - 50, h - 50), (220, 220, 255), cv2.FILLED)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    instructions = [
        "GESTURE CONTROLS",
        "",
        "Move Mouse        : Index finger",
        "Left Click        : Thumb + Index pinch",
        "Right Click       : Thumb + Middle pinch",
        "Scroll            : Index + Middle",
        "Volume            : Thumb + Pinky",
        "Typing Mode       : Press 'T'",
        "Toggle System     : Press 'C'",
        "",
        "Press 'H' to toggle help"
    ]

    y = 120
    for line in instructions:
        cv2.putText(frame, line, (100, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (50, 50, 50), 2)
        y += 40


if __name__ == "__main__":
    main()