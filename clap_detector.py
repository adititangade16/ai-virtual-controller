"""
clap_detector.py
-------------------
Listens to the microphone on a background thread and detects a "clap"
(a short, sharp burst of loud sound) to toggle the whole system's
Active/Inactive state - like a "Clap On / Clap Off" light switch.

Runs independently of the video loop so it never blocks or slows down
the camera feed.
"""

import threading
import time
import numpy as np

try:
    import sounddevice as sd
    SOUND_AVAILABLE = True
except Exception:
    SOUND_AVAILABLE = False


class ClapDetector:
    def __init__(self, on_clap_callback, threshold=0.5, cooldown=1.0,
                 samplerate=44100, blocksize=1024):
        """
        on_clap_callback : function called with no args every time a clap is detected.
        threshold        : normalized amplitude (roughly 0-1) above which a sound
                            counts as a clap. Raise this if background noise or music
                            triggers false positives; lower it if claps aren't detected.
        cooldown         : minimum seconds between two claps, so one clap can't fire twice.
        """
        self.on_clap_callback = on_clap_callback
        self.threshold = threshold
        self.cooldown = cooldown
        self.samplerate = samplerate
        self.blocksize = blocksize

        self._last_clap_time = 0.0
        self._thread = None
        self._running = False

    def _audio_callback(self, indata, frames, time_info, status):
        """Called automatically by sounddevice for every incoming audio block."""
        volume_norm = np.linalg.norm(indata) / (len(indata) ** 0.5)
        if volume_norm > self.threshold:
            now = time.time()
            if now - self._last_clap_time > self.cooldown:
                self._last_clap_time = now
                self.on_clap_callback()

    def start(self):
        """Begins listening for claps on a daemon background thread."""
        if not SOUND_AVAILABLE:
            print("[ClapDetector] 'sounddevice' not available - clap detection disabled. "
                  "You can still toggle the system with the 'c' key.")
            return

        self._running = True

        def _run():
            try:
                with sd.InputStream(callback=self._audio_callback,
                                     channels=1,
                                     samplerate=self.samplerate,
                                     blocksize=self.blocksize):
                    while self._running:
                        time.sleep(0.1)
            except Exception as e:
                print(f"[ClapDetector] Microphone error: {e}. "
                      "Clap detection disabled - use the 'c' key instead.")

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the background listening thread cleanly."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
