import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
from utils.filters import PointFilter
from gestures.detector import GestureDetector

class VisionEngine:
    def __init__(self, model_path='models/hand_landmarker.task'):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.filters = {
            "Left": PointFilter(alpha=0.1, beta=0.01),
            "Right": PointFilter(alpha=0.1, beta=0.01)
        }

    def process_frame(self, frame):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        ts = int(time.time() * 1000)
        
        result = self.landmarker.detect_for_video(mp_image, ts)
        hands_data = []

        if result.hand_landmarks:
            for i in range(len(result.hand_landmarks)):
                landmarks = result.hand_landmarks[i]
                mp_hand = result.handedness[i][0].category_name
                handedness = "Left" if mp_hand == "Right" else "Right"
                
                fingers = self._get_finger_states(landmarks, handedness)
                gesture = GestureDetector.classify(landmarks, fingers, handedness)
                
                raw_x, raw_y = landmarks[8].x, landmarks[8].y
                fx, fy = self.filters[handedness].apply(raw_x * 1000, raw_y * 1000)
                
                hands_data.append({
                    'hand': handedness,
                    'gesture': gesture,
                    'x': fx / 1000,
                    'y': fy / 1000,
                    'landmarks': landmarks
                })
        return hands_data

    def _get_finger_states(self, landmarks, handedness):
        fingers = []
        if handedness == 'Right':
            fingers.append(landmarks[4].x < landmarks[3].x)
        else:
            fingers.append(landmarks[4].x > landmarks[3].x)

        for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
            fingers.append(landmarks[tip].y < landmarks[pip].y)
        return fingers

    def close(self):
        self.landmarker.close()
