"""
gesture_controller.py
------------------------
Turns raw hand landmarks into real mouse actions (move, left-click, right-click,
scroll). Volume and typing are handled by their own dedicated modules, but the
gesture *routing* (which mode is active) lives in main.py.

Gesture map (also see README.md):
    Index finger only up            -> Move mouse
    Thumb + Index pinch (in Mouse)  -> Left click
    Thumb + Middle pinch (in Mouse) -> Right click
    Index + Middle both up          -> Scroll mode (move hand up/down to scroll)
"""

import time
import pyautogui

from utils import Smoother, map_range

# We manage screen edges ourselves via clamping, so disable PyAutoGUI's
# corner fail-safe to avoid accidental aborts when the cursor nears a corner.
pyautogui.FAILSAFE = False
# Removes PyAutoGUI's default tiny delay after every call - big FPS win for
# a real-time loop that calls moveTo() dozens of times per second.
pyautogui.PAUSE = 0


class GestureController:
    def __init__(self, frame_width, frame_height, smoothing=0.5, frame_reduction=100):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_reduction = frame_reduction  # margin so the full screen stays reachable
        self.screen_width, self.screen_height = pyautogui.size()

        self.smoother = Smoother(smoothing_factor=smoothing)

        self.click_cooldown = 0.35          # seconds between clicks, avoids double firing
        self.last_click_time = 0
        self.last_right_click_time = 0
        self.click_flash_until = 0          # used by main.py to draw a short "flash" animation

        self.scroll_prev_y = None
        self.current_gesture_label = "Idle"

    # ------------------------------------------------------------------
    def move_mouse(self, index_finger_pos):
        """Maps the index fingertip position (from the reduced camera box) to screen coordinates."""
        x, y = index_finger_pos

        screen_x = map_range(x, self.frame_reduction, self.frame_width - self.frame_reduction,
                              0, self.screen_width)
        screen_y = map_range(y, self.frame_reduction, self.frame_height - self.frame_reduction,
                              0, self.screen_height)

        smooth_x, smooth_y = self.smoother.smooth(screen_x, screen_y)

        # Clamp so we never try to move the cursor off-screen
        smooth_x = max(0, min(self.screen_width - 1, smooth_x))
        smooth_y = max(0, min(self.screen_height - 1, smooth_y))

        pyautogui.moveTo(smooth_x, smooth_y)
        self.current_gesture_label = "Moving"

    def left_click(self) -> bool:
        """Performs a left click if the cooldown has elapsed. Returns True if it actually fired."""
        now = time.time()
        if now - self.last_click_time > self.click_cooldown:
            pyautogui.click(button="left")
           
            self.last_click_time = now
            self.click_flash_until = now + 0.25
            self.current_gesture_label = "Left Click"
            return True
        return False

    def right_click(self) -> bool:
        """Performs a right click if the cooldown has elapsed. Returns True if it actually fired."""
        now = time.time()
        if now - self.last_right_click_time > self.click_cooldown:
            pyautogui.click(button="right")
            
            self.last_right_click_time = now
            self.click_flash_until = now + 0.25
            self.current_gesture_label = "Right Click"
            return True
        return False

    def scroll(self, current_y):
        """Scrolls based on vertical hand movement while in Scroll Mode."""
        if self.scroll_prev_y is None:
            self.scroll_prev_y = current_y
            return

        delta = self.scroll_prev_y - current_y
        if abs(delta) > 5:  # dead-zone to avoid jittery, accidental scrolling
            pyautogui.scroll(int(delta * 2))
            self.current_gesture_label = "Scrolling"
        self.scroll_prev_y = current_y

    def reset_scroll(self):
        """Call whenever leaving Scroll Mode so the next entry doesn't cause a jump."""
        self.scroll_prev_y = None
