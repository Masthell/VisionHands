"""
Модуль отслеживания рук с помощью MediaPipe Tasks API.
Определяет положение рук, состояние пальцев и жесты.
"""

import cv2
import mediapipe as mp
import numpy as np
import os

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from settings_manager import get_resource_dir


class HandTracker:
    """Класс для отслеживания рук через MediaPipe Hand Landmarker."""

    # Индексы кончиков пальцев
    FINGER_TIPS = [4, 8, 12, 16, 20]
    FINGER_PIPS = [3, 6, 10, 14, 18]

    # Соединения между landmarks для рисования
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),        # Большой палец
        (0, 5), (5, 6), (6, 7), (7, 8),        # Указательный
        (5, 9), (9, 10), (10, 11), (11, 12),   # Средний
        (9, 13), (13, 14), (14, 15), (15, 16), # Безымянный
        (13, 17), (17, 18), (18, 19), (19, 20),# Мизинец
        (0, 17)                                  # Ладонь
    ]

    def __init__(self, model_path='models/hand_landmarker.task',
                 max_hands=2, detection_conf=0.5, tracking_conf=0.5):
        """
        Инициализация трекера рук.

        Args:
            model_path: Путь к файлу модели (относительно папки ресурсов)
            max_hands: Максимальное количество рук
            detection_conf: Минимальная уверенность детекции
            tracking_conf: Минимальная уверенность трекинга

        Raises:
            FileNotFoundError: Если файл модели не найден
        """
        # Используем get_resource_dir() — работает и в IDE, и в .exe
        base_dir = get_resource_dir()
        full_model_path = os.path.join(base_dir, model_path)

        if not os.path.exists(full_model_path):
            raise FileNotFoundError(
                f"Модель не найдена: {full_model_path}\n"
                f"Скачайте hand_landmarker.task и поместите в папку models/"
            )

        with open(full_model_path, 'rb') as f:
            model_data = f.read()

        base_options = python.BaseOptions(
            model_asset_buffer=model_data
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_conf,
            min_hand_presence_confidence=detection_conf,
            min_tracking_confidence=tracking_conf
        )

        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.timestamp_ms = 0

    def detect(self, frame):
        """
        Обнаружить руки на кадре.

        Args:
            frame: BGR кадр с камеры

        Returns:
            result: HandLandmarkerResult (hand_landmarks, handedness)
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self.timestamp_ms += 33  # ~30 FPS
        result = self.landmarker.detect_for_video(mp_image, self.timestamp_ms)
        return result

    def get_finger_states(self, landmarks, handedness='Right'):
        """
        Определить, какие пальцы подняты.

        Args:
            landmarks: Список NormalizedLandmark одной руки
            handedness: 'Right' или 'Left'

        Returns:
            list[bool]: [большой, указательный, средний, безымянный, мизинец]
        """
        fingers = []

        # Большой палец — по X
        if handedness == 'Right':
            fingers.append(landmarks[self.FINGER_TIPS[0]].x < landmarks[self.FINGER_PIPS[0]].x)
        else:
            fingers.append(landmarks[self.FINGER_TIPS[0]].x > landmarks[self.FINGER_PIPS[0]].x)

        # Остальные — по Y (меньше = выше)
        for i in range(1, 5):
            fingers.append(
                landmarks[self.FINGER_TIPS[i]].y < landmarks[self.FINGER_PIPS[i]].y
            )

        return fingers

    def get_landmark_px(self, landmarks, idx, frame_shape):
        """Получить координаты landmark в пикселях."""
        h, w = frame_shape[:2]
        lm = landmarks[idx]
        return int(lm.x * w), int(lm.y * h)

    def get_distance(self, landmarks, idx1, idx2, frame_shape):
        """Расстояние между двумя landmarks в пикселях."""
        x1, y1 = self.get_landmark_px(landmarks, idx1, frame_shape)
        x2, y2 = self.get_landmark_px(landmarks, idx2, frame_shape)
        return np.hypot(x2 - x1, y2 - y1)

    def draw_landmarks(self, frame, landmarks):
        """Нарисовать landmarks руки на кадре."""
        h, w = frame.shape[:2]

        # Рисуем соединения
        for connection in self.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            x1 = int(landmarks[start_idx].x * w)
            y1 = int(landmarks[start_idx].y * h)
            x2 = int(landmarks[end_idx].x * w)
            y2 = int(landmarks[end_idx].y * h)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Рисуем точки
        for lm in landmarks:
            x = int(lm.x * w)
            y = int(lm.y * h)
            cv2.circle(frame, (x, y), 5, (0, 255, 255), -1)
            cv2.circle(frame, (x, y), 5, (0, 200, 200), 1)

    def close(self):
        """Освободить ресурсы."""
        self.landmarker.close()
