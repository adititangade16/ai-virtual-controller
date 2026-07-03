"""
volume_control.py
--------------------
Controls the system's master volume using pycaw (a Python wrapper around
Windows' Core Audio API).

NOTE: pycaw only works on Windows. On macOS/Linux this module automatically
falls back to a "simulated" mode (it still computes the percentage, it just
doesn't apply it to the OS) so the rest of the app keeps running without
crashing. To add real volume control on Mac you'd shell out to `osascript
-e "set volume output volume X"`; on Linux you'd use `amixer` or `pactl`.
"""

import numpy as np

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except (ImportError, OSError):
    PYCAW_AVAILABLE = False


class VolumeController:
    def __init__(self):
        self.available = PYCAW_AVAILABLE
        self.volume_interface = None
        self.min_vol, self.max_vol = -65.0, 0.0  # pycaw reports volume in dB
        self._simulated_percent = 50             # used when pycaw is unavailable

        if self.available:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
                vol_range = self.volume_interface.GetVolumeRange()
                self.min_vol, self.max_vol = vol_range[0], vol_range[1]
            except Exception as e:
                print(f"[VolumeControl] Could not initialize pycaw ({e}). Running in simulated mode.")
                self.available = False

    def set_volume_from_distance(self, hand_distance, min_dist=30, max_dist=250) -> int:
        """
        Maps a hand-span distance (in pixels, typically thumb-to-pinky) to a
        system volume percentage (0-100) and applies it.

        min_dist / max_dist: calibrate these to your camera's resolution and
        your comfortable hand-span range if volume feels too sensitive or dead.
        """
        clamped = max(min_dist, min(max_dist, hand_distance))
        percent = np.interp(clamped, [min_dist, max_dist], [0, 100])

        if self.available and self.volume_interface:
            vol_db = np.interp(percent, [0, 100], [self.min_vol, self.max_vol])
            self.volume_interface.SetMasterVolumeLevel(vol_db, None)
        else:
            self._simulated_percent = percent

        return int(percent)

    def get_volume_percent(self) -> int:
        if self.available and self.volume_interface:
            current_db = self.volume_interface.GetMasterVolumeLevel()
            return int(np.interp(current_db, [self.min_vol, self.max_vol], [0, 100]))
        return int(self._simulated_percent)
