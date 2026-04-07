"""
Модуль управления компьютером жестами рук.
Правая рука — курсор, левая рука — клик.
"""

import pyautogui
import numpy as np
import time


# Настройки PyAutoGUI
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


class GestureController:
    """Класс для управления компьютером через жесты рук.
    
    Правая рука: указательный палец → перемещение курсора.
    Левая рука: указательный палец → клик.
    Скролл: правая рука, указательный + средний палец.
    Правый клик: кулак правой руки (3 кадра подряд).
    """

    def __init__(self, screen_w=None, screen_h=None, smoothing=5,
                 click_cooldown=0.4, right_click_cooldown=0.8, scroll_speed=5):
        """
        Инициализация контроллера.

        Args:
            screen_w, screen_h: Размеры экрана (авто если None)
            smoothing: Кадров для сглаживания курсора
            click_cooldown: Задержка между кликами (сек)
            right_click_cooldown: Задержка между правыми кликами (сек)
            scroll_speed: Делитель скорости скролла
        """
        if screen_w is None or screen_h is None:
            self.screen_w, self.screen_h = pyautogui.size()
        else:
            self.screen_w = screen_w
            self.screen_h = screen_h

        self.smoothing = smoothing
        self.cursor_history = []
        self.last_click_time = 0.0
        self.click_cooldown = click_cooldown
        self.last_right_click_time = 0.0
        self.right_click_cooldown = right_click_cooldown
        self.last_scroll_y = None
        self.scroll_speed = scroll_speed

        # Дебаунс кулака (right_click)
        self.fist_frame_count = 0
        self.fist_threshold = 3


        # Текущие жесты для HUD
        self.right_gesture = "none"
        self.left_gesture = "none"

    def process_right_hand(self, finger_states, landmarks, frame_shape, hand_tracker):
        """
        Обработка правой руки — курсор и скролл.

        Args:
            finger_states: Состояния пальцев [большой, указательный, средний, безымянный, мизинец]
            landmarks: Список NormalizedLandmark руки
            frame_shape: (h, w, c)
            hand_tracker: Экземпляр HandTracker

        Returns:
            str: Название жеста
        """
        if finger_states is None:
            self.right_gesture = "none"
            return "none"

        thumb, index, middle, ring, pinky = finger_states


        # Указательный + средний = СКРОЛЛ
        if index and middle and not ring and not pinky:
            self._perform_scroll(landmarks, frame_shape, hand_tracker)
            self.fist_frame_count = 0

            self.right_gesture = "scroll"
            return "scroll"

        # Указательный = КУРСОР
        if index and not middle and not ring and not pinky:
            self._move_cursor(landmarks, frame_shape, hand_tracker)
            self.last_scroll_y = None
            self.fist_frame_count = 0

            self.right_gesture = "pointer"
            return "pointer"

        # Кулак = ПРАВЫЙ КЛИК (проверяем только 4 пальца без большого)
        if not any(finger_states[1:]):
            self.fist_frame_count += 1
            if self.fist_frame_count >= self.fist_threshold:
                self._perform_right_click()
            self.last_scroll_y = None

            self.right_gesture = "right_click"
            return "right_click"

        self.last_scroll_y = None
        self.fist_frame_count = 0

        self.right_gesture = "none"
        return "none"

    def process_left_hand(self, finger_states):
        """
        Обработка левой руки — клик.
        Указательный палец поднят = клик.

        Args:
            finger_states: Состояния пальцев

        Returns:
            str: Название жеста
        """
        if finger_states is None:
            self.left_gesture = "none"
            return "none"

        thumb, index, middle, ring, pinky = finger_states

        # Указательный палец = КЛИК
        if index and not middle and not ring and not pinky:
            self._perform_click()
            self.left_gesture = "click"
            return "click"

        self.left_gesture = "none"
        return "none"

    def _move_cursor(self, landmarks, frame_shape, hand_tracker):
        """Переместить курсор по позиции указательного пальца."""
        ix, iy = hand_tracker.get_landmark_px(landmarks, 8, frame_shape)
        h, w = frame_shape[:2]

        margin_x = w * 0.1
        margin_y = h * 0.1
        nx = (ix - margin_x) / (w - 2 * margin_x)
        ny = (iy - margin_y) / (h - 2 * margin_y)

        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        screen_x = int(nx * self.screen_w)
        screen_y = int(ny * self.screen_h)

        self.cursor_history.append((screen_x, screen_y))
        if len(self.cursor_history) > self.smoothing:
            self.cursor_history.pop(0)

        avg_x = int(np.mean([p[0] for p in self.cursor_history]))
        avg_y = int(np.mean([p[1] for p in self.cursor_history]))

        pyautogui.moveTo(avg_x, avg_y)

    def _perform_click(self):
        """Левый клик с дебаунсом."""
        now = time.time()
        if now - self.last_click_time > self.click_cooldown:
            pyautogui.click()
            self.last_click_time = now

    def _perform_right_click(self):
        """Правый клик с дебаунсом."""
        now = time.time()
        if now - self.last_right_click_time > self.right_click_cooldown:
            pyautogui.rightClick()
            self.last_right_click_time = now

    def _perform_scroll(self, landmarks, frame_shape, hand_tracker):
        """Скролл по движению двух пальцев."""
        _, iy = hand_tracker.get_landmark_px(landmarks, 8, frame_shape)
        _, my = hand_tracker.get_landmark_px(landmarks, 12, frame_shape)
        avg_y = (iy + my) / 2

        if self.last_scroll_y is not None:
            delta = self.last_scroll_y - avg_y
            scroll_amount = int(delta / self.scroll_speed)
            if scroll_amount != 0:
                pyautogui.scroll(scroll_amount)

        self.last_scroll_y = avg_y

