"""
utils.py
---------
Small shared helpers and the pastel color palette used across every module.
Centralizing these avoids repeating "magic numbers" and keeps the UI consistent.
"""

import sys
import time
import math


# ---------------------------------------------------------------------------
# COLOR PALETTE (soft pastel theme - OpenCV uses BGR, not RGB!)
# ---------------------------------------------------------------------------
COLOR_BG_PANEL   = (235, 240, 245)   # soft cream / off-white panel background
COLOR_PRIMARY    = (245, 172, 219)   # pastel purple/pink - main accent & labels
COLOR_SECONDARY  = (174, 235, 207)   # pastel mint - secondary accent
COLOR_ACCENT     = (186, 210, 255)   # pastel peach - highlights, hover, flashes
COLOR_ACTIVE     = (150, 219, 170)   # soft green  - "Active" status dot
COLOR_INACTIVE   = (140, 140, 220)   # soft red    - "Inactive" status dot
COLOR_TEXT_DARK  = (60, 60, 60)
COLOR_TEXT_LIGHT = (250, 250, 250)
COLOR_LANDMARK   = (160, 190, 245)   # pastel landmark dots
COLOR_CONNECTION = (245, 200, 220)   # pastel lines connecting landmarks


class FPSCounter:
    """Exponentially-smoothed FPS counter so the on-screen number doesn't jitter every frame."""

    def __init__(self, smoothing: float = 0.9):
        self._prev_time = time.time()
        self._fps = 0.0
        self._smoothing = smoothing

    def update(self) -> float:
        """Call exactly once per frame. Returns the current smoothed FPS."""
        now = time.time()
        dt = now - self._prev_time
        self._prev_time = now
        if dt > 0:
            instant_fps = 1.0 / dt
            self._fps = (self._smoothing * self._fps) + ((1 - self._smoothing) * instant_fps)
        return self._fps


class Smoother:
    """
    Exponential moving average smoother - reduces the natural jitter of hand-tracked
    coordinates so the mouse cursor glides instead of shaking.

    smoothing_factor closer to 1.0 -> snappier, more responsive, more jitter.
    smoothing_factor closer to 0.0 -> smoother, less jitter, slightly more lag.
    """

    def __init__(self, smoothing_factor: float = 0.5):
        self.smoothing_factor = smoothing_factor
        self.prev_x = None
        self.prev_y = None

    def smooth(self, x: float, y: float):
        if self.prev_x is None:
            self.prev_x, self.prev_y = x, y
        smooth_x = self.prev_x + (x - self.prev_x) * self.smoothing_factor
        smooth_y = self.prev_y + (y - self.prev_y) * self.smoothing_factor
        self.prev_x, self.prev_y = smooth_x, smooth_y
        return smooth_x, smooth_y

    def reset(self):
        self.prev_x = None
        self.prev_y = None


def distance(p1, p2) -> float:
    """Euclidean distance between two (x, y) points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def map_range(value, in_min, in_max, out_min, out_max):
    """Maps a value from one numeric range to another, clamping at both ends."""
    value = max(min(value, in_max), in_min)
    return out_min + (float(value - in_min) / float(in_max - in_min)) * (out_max - out_min)


def play_beep():
    """
    Lightweight, best-effort sound feedback for actions (click, keypress, etc).
    Uses winsound on Windows (no extra dependency); falls back to a terminal
    bell on Mac/Linux so the app never crashes because of this cosmetic feature.
    """
    try:
        if sys.platform.startswith("win"):
            import winsound
            winsound.Beep(1000, 60)
        else:
            print('\a', end='', flush=True)
    except Exception:
        pass  # sound feedback is a nice-to-have, never let it break the app
