"""
Модуль аутентификации по жестам.
Проверяет последовательность жестов перед запуском приложения.

Жесты (finger_states: [большой, указательный, средний, безымянный, мизинец]):
  "one"   - только указательный       [_, 1, 0, 0, 0]
  "two"   - указательный + средний    [_, 1, 1, 0, 0]
  "three" - указ+сред+безымянный      [_, 1, 1, 1, 0]
  "four"  - все кроме большого        [_, 1, 1, 1, 1]
  "fist"  - кулак                     [_, 0, 0, 0, 0]
  "ok"    - большой + мизинец         [1, 0, 0, 0, 1]
  "rock"  - указательный + мизинец    [_, 1, 0, 0, 1]
  "open"  - все пальцы                [1, 1, 1, 1, 1]
"""

import cv2
import time


# =====================================================================
#  НАСТРОЙКИ ПАРОЛЯ
#  Измени эту последовательность на свою:
# =====================================================================
PASSWORD_SEQUENCE = ["one", "fist", "two", "rock"]
# =====================================================================


# Подписи жестов (только ASCII — OpenCV не поддерживает Unicode/эмодзи)
GESTURE_LABELS = {
    "one":   "ONE   [index finger]",
    "two":   "TWO   [index + middle]",
    "three": "THREE [3 fingers]",
    "four":  "FOUR  [4 fingers]",
    "fist":  "FIST  [closed hand]",
    "ok":    "OK    [thumb + pinky]",
    "rock":  "ROCK  [index + pinky]",
    "open":  "OPEN  [all fingers]",
}


def classify_gesture(finger_states):
    """
    Определяет жест по состоянию пальцев.

    Args:
        finger_states: [большой, указательный, средний, безымянный, мизинец] (список bool)

    Returns:
        str: название жеста или None
    """
    if finger_states is None:
        return None

    thumb, index, middle, ring, pinky = finger_states

    # Кулак — ни один палец не поднят (большой не учитывается)
    if not index and not middle and not ring and not pinky:
        return "fist"

    # Rock — указательный + мизинец
    if index and not middle and not ring and pinky:
        return "rock"

    # OK — только большой + мизинец
    if thumb and not index and not middle and not ring and pinky:
        return "ok"

    # ONE — только указательный
    if index and not middle and not ring and not pinky:
        return "one"

    # TWO — указательный + средний
    if index and middle and not ring and not pinky:
        return "two"

    # THREE — указательный + средний + безымянный
    if index and middle and ring and not pinky:
        return "three"

    # FOUR / OPEN — все кроме большого
    if index and middle and ring and pinky:
        return "open"

    return None


class GestureAuth:
    """
    Система аутентификации по жестам.

    Пользователь должен показать правильные жесты по порядку.
    Каждый жест нужно удерживать HOLD_TIME секунд.
    Можно убирать руку между жестами (сброс таймера удержания).
    Нет блокировки — можно пробовать сколько угодно.
    """

    HOLD_TIME = 1.2       # сколько секунд держать жест для подтверждения
    COOLDOWN_AFTER = 1.5  # пауза после шага (игнор всех жестов)

    def __init__(self, password=None):
        self.password = password or PASSWORD_SEQUENCE
        self.reset()

    def reset(self):
        """Сброс состояния аутентификации."""
        self.current_step = 0
        self.current_gesture = None
        self.gesture_start = None
        self.cooldown_until = 0
        self.attempts = 0

    def update(self, gesture):
        """
        Обновляет состояние на основе текущего жеста.

        Args:
            gesture: строка с названием жеста или None

        Returns:
            str: "waiting" | "holding" | "step_ok" | "success" | "wrong"
        """
        now = time.time()

        # Пауза после успешного шага — игнорируем всё,
        # даём пользователю время перейти к следующему жесту
        if now < self.cooldown_until:
            return "holding"

        # Рука не видна — сбрасываем удержание, но не прогресс
        if gesture is None:
            self.current_gesture = None
            self.gesture_start = None
            return "waiting"

        expected = self.password[self.current_step]

        if gesture != self.current_gesture:
            # Жест изменился — начинаем отслеживание заново
            self.current_gesture = gesture
            self.gesture_start = now

        # Только правильный жест учитывается
        # Если держать неправильный долго — сброс последовательности
        # Если быстро показать неправильный — игнорируется
        if gesture == expected:
            held = now - (self.gesture_start or now)
            if held >= self.HOLD_TIME:
                self.current_step += 1
                self.cooldown_until = now + self.COOLDOWN_AFTER
                self.current_gesture = None
                self.gesture_start = None

                if self.current_step >= len(self.password):
                    return "success"
                return "step_ok"
            return "holding"
        else:
            # Неправильный жест — сбрасываем только если держали долго
            held = now - (self.gesture_start or now)
            if held >= self.HOLD_TIME:
                self.current_step = 0
                self.attempts += 1
                self.current_gesture = None
                self.gesture_start = None
                return "wrong"
            return "waiting"

    def get_hold_progress(self):
        """Прогресс удержания от 0.0 до 1.0."""
        if self.gesture_start is None:
            return 0.0
        held = time.time() - self.gesture_start
        return min(1.0, held / self.HOLD_TIME)

    def get_cooldown_remaining(self):
        """Сколько секунд осталось до конца паузы."""
        remaining = self.cooldown_until - time.time()
        return max(0.0, remaining)

    def is_in_cooldown(self):
        """Находится ли сейчас в паузе."""
        return time.time() < self.cooldown_until


# =====================================================================
#  Функция отрисовки экрана аутентификации
# =====================================================================

def draw_auth_screen(frame, auth, status, current_gesture):
    """
    Рисует интерфейс аутентификации поверх кадра с камеры.

    Args:
        frame: кадр (BGR)
        auth: объект GestureAuth
        status: последний статус из auth.update()
        current_gesture: текущий жест или None
    """
    h, w = frame.shape[:2]

    # Размытие фона
    blurred = cv2.GaussianBlur(frame, (31, 31), 0)
    cv2.addWeighted(blurred, 0.85, frame, 0.15, 0, frame)

    font = cv2.FONT_HERSHEY_SIMPLEX

    # --- Заголовок ---
    title = "GESTURE LOCK"
    ts = cv2.getTextSize(title, font, 1.2, 2)[0]
    cv2.putText(frame, title, ((w - ts[0]) // 2, 60), font, 1.2, (0, 200, 255), 2)

    # --- Кружки шагов ---
    n = len(auth.password)
    circle_r = 18
    spacing = 60
    total_w = n * spacing
    start_x = (w - total_w) // 2 + spacing // 2
    cy = 110

    for i in range(n):
        cx = start_x + i * spacing
        if i < auth.current_step:
            # Выполнено — зелёный
            cv2.circle(frame, (cx, cy), circle_r, (0, 220, 80), -1)
            cv2.putText(frame, "OK", (cx - 13, cy + 6), font, 0.45, (0, 0, 0), 1)
        elif i == auth.current_step:
            # Текущий — синий
            cv2.circle(frame, (cx, cy), circle_r, (0, 180, 255), 2)
            cv2.circle(frame, (cx, cy), circle_r - 4, (0, 60, 120), -1)
            cv2.putText(frame, str(i + 1), (cx - 6, cy + 6), font, 0.55, (200, 230, 255), 1)
        else:
            # Будущий — серый
            cv2.circle(frame, (cx, cy), circle_r, (80, 80, 80), 1)
            cv2.putText(frame, str(i + 1), (cx - 6, cy + 6), font, 0.55, (100, 100, 100), 1)

    # --- Подсказка ---
    if auth.current_step < len(auth.password):
        if auth.is_in_cooldown():
            remaining = auth.get_cooldown_remaining()
            hint = "Next gesture in: " + "{:.1f}".format(remaining) + "s  (relax your hand)"
            hs = cv2.getTextSize(hint, font, 0.72, 1)[0]
            cv2.putText(frame, hint, ((w - hs[0]) // 2, 165), font, 0.72, (180, 180, 60), 1)
        else:
            expected = auth.password[auth.current_step]
            hint_label = GESTURE_LABELS.get(expected, expected.upper())
            hint = "Show: " + hint_label
            hs = cv2.getTextSize(hint, font, 0.75, 1)[0]
            cv2.putText(frame, hint, ((w - hs[0]) // 2, 165), font, 0.75, (255, 220, 100), 1)

    # --- Текущий жест ---
    if current_gesture:
        detected_label = GESTURE_LABELS.get(current_gesture, current_gesture.upper())
        dtext = "Detected: " + detected_label
        ds = cv2.getTextSize(dtext, font, 0.65, 1)[0]

        expected_now = auth.password[auth.current_step] if auth.current_step < len(auth.password) else ""
        col = (0, 220, 80) if current_gesture == expected_now else (60, 80, 200)
        cv2.putText(frame, dtext, ((w - ds[0]) // 2, 205), font, 0.65, col, 1)
    else:
        no_hand = "( no hand detected )"
        ns = cv2.getTextSize(no_hand, font, 0.6, 1)[0]
        cv2.putText(frame, no_hand, ((w - ns[0]) // 2, 205), font, 0.6, (100, 100, 100), 1)

    # --- Полоса удержания ---
    if current_gesture and auth.current_gesture == current_gesture:
        progress = auth.get_hold_progress()
        bar_w = w - 120
        bar_x = 60
        bar_y = h - 80
        bar_h = 20

        # Фон
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (40, 40, 40), -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (80, 80, 80), 1)

        # Заполнение
        fill = int(progress * bar_w)
        if fill > 0:
            col_fill = (0, int(100 + 120 * progress), int(200 - 150 * progress))
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill, bar_y + bar_h), col_fill, -1)

        hold_label = "Hold... " + str(int(progress * 100)) + "%"
        cv2.putText(frame, hold_label, (bar_x, bar_y - 8), font, 0.55, (200, 200, 200), 1)

    # --- Сообщения ---
    status_msgs = {
        "step_ok": ("Step confirmed!", (0, 220, 80)),
        "wrong":   ("Wrong gesture! Try again.", (80, 60, 220)),
        "success": ("ACCESS GRANTED", (0, 255, 100)),
    }
    if status in status_msgs:
        msg, col = status_msgs[status]
        ms = cv2.getTextSize(msg, font, 0.85, 2)[0]
        cv2.putText(frame, msg, ((w - ms[0]) // 2, h - 120), font, 0.85, col, 2)

    # --- Счётчик попыток ---
    if auth.attempts > 0:
        att_text = "Wrong attempts: " + str(auth.attempts)
        cv2.putText(frame, att_text, (20, h - 20), font, 0.5, (80, 80, 200), 1)

    # --- Подсказка выхода ---
    cv2.putText(frame, "ESC - exit", (w - 120, h - 20), font, 0.45, (100, 100, 100), 1)