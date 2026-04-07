"""
Главный модуль приложения.
Объединяет: камера, трекинг рук, управление жестами.
Правая рука - курсор, левая рука - клик.
"""

import cv2
import time

from hand_tracker import HandTracker
from gesture_controller import GestureController
from settings_manager import SettingsManager
from gesture_auth import GestureAuth, classify_gesture, draw_auth_screen


class App:
    """Основной класс приложения Gesture Controller."""

    def __init__(self, camera_id=0, width=1280, height=720):
        self.settings = SettingsManager()
        cfg = self.settings.get_all()

        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera!")

        self.hand_tracker = HandTracker(
            max_hands=2,
            detection_conf=cfg['detection_confidence']
        )
        self.gesture_controller = GestureController(
            smoothing=cfg['smoothing'],
            click_cooldown=cfg['click_cooldown'],
            right_click_cooldown=cfg['right_click_cooldown'],
            scroll_speed=cfg['scroll_speed']
        )

        self.gesture_enabled = True
        self.prev_time = time.time()
        self.fps = 0

    def _run_auth(self):
        """
        Этап аутентификации по жестам.
        Возвращает True если пользователь прошёл, False если вышел.
        """
        print("=" * 50)
        print("  GESTURE LOCK - enter your gesture password")
        print("=" * 50)

        auth = GestureAuth()
        last_status = "waiting"
        status_reset_time = None

        while True:
            ret, frame = self.cap.read()
            if not ret:
                return False

            frame = cv2.flip(frame, 1)

            hand_result = self.hand_tracker.detect(frame)
            current_gesture = None

            if hand_result.hand_landmarks:
                landmarks = hand_result.hand_landmarks[0]
                handedness = 'Right'
                if hand_result.handedness:
                    handedness = hand_result.handedness[0][0].category_name

                self.hand_tracker.draw_landmarks(frame, landmarks)
                finger_states = self.hand_tracker.get_finger_states(landmarks, handedness)
                current_gesture = classify_gesture(finger_states)

            status = auth.update(current_gesture)
            if status in ("step_ok", "wrong", "success"):
                last_status = status
                status_reset_time = time.time() + 1.2

            draw_auth_screen(frame, auth, last_status, current_gesture)

            cv2.imshow("Gesture Controller", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 27 or key == ord('q'):
                return False

            if status == "success":
                success_until = time.time() + 1.5
                while time.time() < success_until:
                    ret, frame = self.cap.read()
                    if not ret:
                        break
                    frame = cv2.flip(frame, 1)
                    draw_auth_screen(frame, auth, "success", None)
                    cv2.imshow("Gesture Controller", frame)
                    cv2.waitKey(1)
                print("Authentication passed!")
                return True

            # Сброс отображения статуса через некоторое время
            if status_reset_time and time.time() > status_reset_time:
                last_status = "waiting"
                status_reset_time = None

    def run(self):
        """Основной цикл приложения."""
        print("=" * 50)
        print("  GESTURE CONTROLLER")
        print("=" * 50)
        print("  Right hand - cursor / scroll")
        print("  Left hand  - click")
        print("  G - toggle gestures on/off")
        print("  Q / ESC - exit")
        print("=" * 50)

        # --- Аутентификация ---
        if not self._run_auth():
            self._cleanup()
            return

        print("=" * 50)
        print("  Password accepted. Application started.")
        print("=" * 50)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Camera read error!")
                break

            frame = cv2.flip(frame, 1)

            hand_result = self.hand_tracker.detect(frame)

            if hand_result.hand_landmarks:
                for i, landmarks in enumerate(hand_result.hand_landmarks):
                    handedness = 'Right'
                    if hand_result.handedness and i < len(hand_result.handedness):
                        handedness = hand_result.handedness[i][0].category_name

                    self.hand_tracker.draw_landmarks(frame, landmarks)
                    finger_states = self.hand_tracker.get_finger_states(landmarks, handedness)

                    if self.gesture_enabled:
                        if handedness == 'Right':
                            self.gesture_controller.process_right_hand(
                                finger_states, landmarks, frame.shape, self.hand_tracker
                            )
                        elif handedness == 'Left':
                            self.gesture_controller.process_left_hand(finger_states)

            self._draw_hud(frame)

            cv2.imshow("Gesture Controller", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('g'):
                self.gesture_enabled = not self.gesture_enabled
                print("Gestures: " + ("ON" if self.gesture_enabled else "OFF"))

        self._cleanup()

    def _draw_hud(self, frame):
        """Рисует HUD (информационную панель)."""
        curr_time = time.time()
        self.fps = 1.0 / (curr_time - self.prev_time + 1e-9)
        self.prev_time = curr_time

        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

        font = cv2.FONT_HERSHEY_SIMPLEX
        s = 0.6
        white = (255, 255, 255)
        green = (0, 255, 0)
        red = (0, 0, 255)
        cyan = (0, 255, 255)

        y = 35
        cv2.putText(frame, "FPS: " + str(int(self.fps)), (20, y), font, s, white, 1)
        y += 30

        g_status = ("ON", green) if self.gesture_enabled else ("OFF", red)
        cv2.putText(frame, "[G] Gestures: ", (20, y), font, s, white, 1)
        cv2.putText(frame, g_status[0], (210, y), font, s, g_status[1], 2)
        y += 30

        gesture_names = {
            "none": "---", "pointer": "Cursor", "click": "Click!",
            "scroll": "Scroll", "right_click": "Right Click!"
        }

        right_text = gesture_names.get(self.gesture_controller.right_gesture, "---")
        left_text = gesture_names.get(self.gesture_controller.left_gesture, "---")

        cv2.putText(frame, "Right: " + right_text, (20, y), font, s, cyan, 1)
        y += 30
        cv2.putText(frame, "Left: " + left_text, (20, y), font, s, cyan, 1)

    def _cleanup(self):
        """Освобождает ресурсы."""
        self.cap.release()
        self.hand_tracker.close()
        cv2.destroyAllWindows()
        print("Application closed.")
