from gestures.actions import MoveCursorAction, ClickAction, ScrollAction, KeyPressAction
from utils.db_manager import SettingsDB
import pyautogui
import time

class Action:
    def execute(self, *args, **kwargs): pass

class GestureProfile:
    def __init__(self):
        screen_w, screen_h = pyautogui.size()
        db = SettingsDB()
        sens = db.get('mouse_sensitivity')
        
        self.name = "Default"
        self.move_action = MoveCursorAction(screen_w, screen_h, sensitivity=sens)
        self.left_click = ClickAction(button='left')
        self.right_click = ClickAction(button='right')
        self.scroll_action = ScrollAction(sensitivity=15)

        self.right_hand_map = {
            "POINTER": self.move_action
        }
        self.left_hand_map = {
            "POINTER": self.left_click,
            "PEACE": self.right_click
        }

    def get_action(self, gesture_name, handedness):
        if handedness == "Right":
            return self.right_hand_map.get(gesture_name)
        return self.left_hand_map.get(gesture_name)

class YouTubeProfile(GestureProfile):
    def __init__(self):
        super().__init__()
        self.name = "YouTube"
        self.right_hand_map["FIST"] = KeyPressAction('space')
        self.left_hand_map["FIST"] = KeyPressAction('n')

class GlobalShortcuts:
    def __init__(self):
        self.last_time = 0
        self.cooldown = 1.0

    def check(self, left_gesture, right_gesture):
        now = time.time()
        if now - self.last_time < self.cooldown:
            return

        if left_gesture == "FIST" and right_gesture == "FIST":
            pyautogui.hotkey('alt', 'tab')
            self.last_time = now
