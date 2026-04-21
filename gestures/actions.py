import pyautogui
import time

pyautogui.PAUSE = 0
pyautogui.MINIMUM_DURATION = 0
pyautogui.FAILSAFE = False

class Action:
    def execute(self, *args, **kwargs):
        pass

class MoveCursorAction(Action):
    def __init__(self, screen_w, screen_h, sensitivity=1.25):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.last_x, self.last_y = -1, -1
        self.threshold = 1
        self.sensitivity = sensitivity

    def execute(self, x_norm, y_norm):
        shifted_x = 0.5 + (x_norm - 0.5) * self.sensitivity
        shifted_y = 0.5 + (y_norm - 0.5) * self.sensitivity
        shifted_x = max(0.0, min(1.0, shifted_x))
        shifted_y = max(0.0, min(1.0, shifted_y))
        target_x = int(shifted_x * self.screen_w)
        target_y = int(shifted_y * self.screen_h)
        if abs(target_x - self.last_x) > self.threshold or abs(target_y - self.last_y) > self.threshold:
            pyautogui.moveTo(target_x, target_y)
            self.last_x, self.last_y = target_x, target_y

class ClickAction(Action):
    def __init__(self, button='left'):
        self.button = button
        self.last_time = 0
        self.cooldown = 0.4
    def execute(self):
        now = time.time()
        if now - self.last_time > self.cooldown:
            pyautogui.click(button=self.button)
            self.last_time = now

class ScrollAction(Action):
    def __init__(self, sensitivity=15):
        self.prev_y = None
        self.sensitivity = sensitivity
    def execute(self, current_y):
        if self.prev_y is not None:
            delta = self.prev_y - current_y
            scroll_amount = int(delta * self.sensitivity)
            if scroll_amount != 0:
                pyautogui.scroll(scroll_amount)
        self.prev_y = current_y
    def reset(self):
        self.prev_y = None

class KeyPressAction(Action):
    def __init__(self, key, cooldown=0.8):
        self.key = key
        self.last_time = 0
        self.cooldown = cooldown
    def execute(self):
        now = time.time()
        if now - self.last_time > self.cooldown:
            pyautogui.press(self.key)
            self.last_time = now
