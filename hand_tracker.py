"""
hand_tracker.py
-----------------
Wraps Google's MediaPipe Hands solution into a simple, reusable class.
Keeps all MediaPipe-specific code in one place so the rest of the project
doesn't need to know how MediaPipe works internally.
"""

import math
import cv2
import mediapipe as mp

from utils import COLOR_LANDMARK, COLOR_CONNECTION


class HandTracker:
    def __init__(self, max_hands=1, detection_confidence=0.7, tracking_confidence=0.7):
        """
        max_hands: limit to 1 hand for speed (tracking 2 hands roughly doubles cost)
        detection_confidence / tracking_confidence: higher = fewer false positives,
            but too high can miss fast movements. 0.7 is a good practical balance.
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.results = None
        # Landmark indices for the 5 fingertips (MediaPipe's 21-point hand model)
        self.tip_ids = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky

    def find_hands(self, frame, draw=True):
        """Detect hands in a BGR frame and optionally draw custom pastel landmarks on it."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(rgb_frame)

        if self.results.multi_hand_landmarks and draw:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self._draw_custom_landmarks(frame, hand_landmarks)
        return frame

    def _draw_custom_landmarks(self, frame, hand_landmarks):
        """Draws a clean, pastel-themed skeleton instead of MediaPipe's default bright colors."""
        h, w, _ = frame.shape

        for start_idx, end_idx in self.mp_hands.HAND_CONNECTIONS:
            x1, y1 = int(hand_landmarks.landmark[start_idx].x * w), int(hand_landmarks.landmark[start_idx].y * h)
            x2, y2 = int(hand_landmarks.landmark[end_idx].x * w), int(hand_landmarks.landmark[end_idx].y * h)
            cv2.line(frame, (x1, y1), (x2, y2), COLOR_CONNECTION, 2)

        for lm in hand_landmarks.landmark:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (cx, cy), 5, COLOR_LANDMARK, cv2.FILLED)

    def find_positions(self, frame, hand_no=0):
        """
        Returns a list of [id, x, y] for each of the 21 landmarks of the requested hand,
        in pixel coordinates. Returns an empty list if no hand is detected.
        """
        landmark_list = []
        if self.results and self.results.multi_hand_landmarks:
            if hand_no < len(self.results.multi_hand_landmarks):
                hand = self.results.multi_hand_landmarks[hand_no]
                h, w, _ = frame.shape
                for idx, lm in enumerate(hand.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    landmark_list.append([idx, cx, cy])
        return landmark_list

    def fingers_up(self, landmark_list):
        """
        Returns a list of 5 booleans [thumb, index, middle, ring, pinky] indicating
        whether each finger is extended ("up"). Uses simple coordinate comparisons -
        fast and reliable for an upright, front-facing hand.

        NOTE: the thumb check is a simplified heuristic that assumes the palm faces
        the camera (works best for a right hand held naturally). This keeps the logic
        easy to read; a production app would also use handedness info from MediaPipe.
        """
        if not landmark_list or len(landmark_list) < 21:
            return [False, False, False, False, False]

        fingers = []

        # Thumb: moves horizontally, not vertically, so compare x-coordinates.
        fingers.append(landmark_list[self.tip_ids[0]][1] > landmark_list[self.tip_ids[0] - 1][1])

        # Other 4 fingers: tip above its PIP joint (smaller y = higher up on screen).
        for tip_id in self.tip_ids[1:]:
            fingers.append(landmark_list[tip_id][2] < landmark_list[tip_id - 2][2])

        return fingers

    @staticmethod
    def find_distance(p1, p2, frame=None, draw=False, color=(219, 172, 245)):
        """Euclidean distance between two [id, x, y] landmark points, with optional drawing."""
        x1, y1 = p1[1], p1[2]
        x2, y2 = p2[1], p2[2]
        length = math.hypot(x2 - x1, y2 - y1)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw and frame is not None:
            cv2.circle(frame, (x1, y1), 8, color, cv2.FILLED)
            cv2.circle(frame, (x2, y2), 8, color, cv2.FILLED)
            cv2.line(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, (cx, cy), 6, color, cv2.FILLED)

        return length, (cx, cy)

    def close(self):
        """Release MediaPipe resources cleanly on app shutdown."""
        self.hands.close()
