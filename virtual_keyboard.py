import time
import cv2
import pyautogui

from utils import COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT, COLOR_TEXT_DARK, COLOR_BG_PANEL, play_beep

KEY_ROWS = [
    list("1234567890"),
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]


class Key:
    def __init__(self, x, y, w, h, text):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.text = text

    def contains(self, px, py):
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h


class VirtualKeyboard:
    def __init__(self, frame_width, frame_height, dwell_time=0.7):
        self.dwell_time = dwell_time
        self.typed_text = ""

        # 🔥 spacing control
        self.gap = 5
        self.side_margin = 20

        self._hover_key = None
        self._hover_start_time = 0.0

        self.keys = []

        key_height = 65
        start_y = frame_height - 320

        # 🔥 PERFECT CENTERED KEYBOARD
        for row_idx, row in enumerate(KEY_ROWS):
            total_keys = len(row)

            usable_width = frame_width - (2 * self.side_margin)
            key_width = int((usable_width - (total_keys - 1) * self.gap) / total_keys)

            y = start_y + row_idx * (key_height + self.gap)

            for col_idx, char in enumerate(row):
                x = self.side_margin + col_idx * (key_width + self.gap)
                self.keys.append(Key(x, y, key_width, key_height, char))

        # 🔥 SPACE + DEL (proper alignment)
        bottom_y = start_y + len(KEY_ROWS) * (key_height + self.gap)

        space_width = int(frame_width * 0.5)
        del_width = int(frame_width * 0.18)

        self.space_key = Key(
            (frame_width - space_width) // 2,
            bottom_y,
            space_width,
            key_height,
            "SPACE"
        )

        self.backspace_key = Key(
            frame_width - del_width - self.side_margin,
            bottom_y,
            del_width,
            key_height,
            "DEL"
        )

    def _all_keys(self):
        return self.keys + [self.space_key, self.backspace_key]

    def draw(self, frame):
        overlay = frame.copy()

        # 🔥 GLASS BACKGROUND
        for key in self._all_keys():
            cv2.rectangle(
                overlay,
                (key.x, key.y),
                (key.x + key.w, key.y + key.h),
                COLOR_BG_PANEL,
                cv2.FILLED
            )

        cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

        # 🔥 DRAW KEYS
        for key in self._all_keys():
            cv2.rectangle(
                frame,
                (key.x, key.y),
                (key.x + key.w, key.y + key.h),
                COLOR_PRIMARY,
                2
            )

            font_scale = 0.8 if len(key.text) == 1 else 0.6

            text_size = cv2.getTextSize(
                key.text,
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                2
            )[0]

            tx = key.x + (key.w - text_size[0]) // 2
            ty = key.y + (key.h + text_size[1]) // 2

            cv2.putText(
                frame,
                key.text,
                (tx, ty),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                COLOR_TEXT_DARK,
                2
            )

        return frame

    def update(self, frame, fingertip_pos):
        if fingertip_pos is None:
            self._hover_key = None
            return None

        px, py = fingertip_pos
        pressed_char = None

        hovered = next((k for k in self._all_keys() if k.contains(px, py)), None)

        if hovered:
            if self._hover_key is hovered:
                elapsed = time.time() - self._hover_start_time
                progress = min(elapsed / self.dwell_time, 1.0)

                # 🔵 progress circle
                cv2.circle(frame, (px, py), 20, COLOR_SECONDARY, 2)
                cv2.ellipse(
                    frame,
                    (px, py),
                    (20, 20),
                    -90,
                    0,
                    int(360 * progress),
                    COLOR_ACCENT,
                    4
                )

                # 🔥 MODERN HOVER EFFECT
                cv2.rectangle(
                    frame,
                    (hovered.x, hovered.y),
                    (hovered.x + hovered.w, hovered.y + hovered.h),
                    (255, 220, 180),
                    cv2.FILLED
                )

                cv2.rectangle(
                    frame,
                    (hovered.x, hovered.y),
                    (hovered.x + hovered.w, hovered.y + hovered.h),
                    (100, 100, 255),
                    2
                )

                if progress >= 1.0:
                    pressed_char = self._fire_key(hovered)
                    self._hover_key = None
            else:
                self._hover_key = hovered
                self._hover_start_time = time.time()
        else:
            self._hover_key = None

        return pressed_char

    def _fire_key(self, key):
        play_beep()

        if key.text == "SPACE":
            pyautogui.press("space")
            self.typed_text += " "
            return " "

        elif key.text == "DEL":
            pyautogui.press("backspace")
            self.typed_text = self.typed_text[:-1]
            return "DEL"

        else:
            pyautogui.press(key.text.lower())
            self.typed_text += key.text
            return key.text