import time
import cv2
from core.camera import CameraStream
from core.engine import VisionEngine
from ui.overlay import HUD
from core.auth import AuthSystem
from utils.window_manager import get_active_app_mode
from gestures.profiles import GestureProfile, YouTubeProfile, GlobalShortcuts
from utils.db_manager import SettingsDB

class VisionProcessor:
    def __init__(self):
        self.camera = CameraStream(width=640, height=480).start()
        self.engine = VisionEngine()
        self.hud = HUD()
        
        self.profiles = {
            "DEFAULT": GestureProfile(),
            "YOUTUBE": YouTubeProfile()
        }
        self.current_profile = self.profiles["DEFAULT"]
        self.global_shortcuts = GlobalShortcuts()
        
        self.auth = AuthSystem()
        
        db = SettingsDB()
        self.update_settings(db.get('mouse_sensitivity'), db.get('smoothing_beta'))
        
        self.last_profile_check = 0
        self.fps = 0
        self.last_time = time.time()

    def update_settings(self, sensitivity, smoothing):
        for profile in self.profiles.values():
            if hasattr(profile, 'move_action'):
                profile.move_action.sensitivity = sensitivity
        self.engine.filters["Right"].beta = smoothing
        self.engine.filters["Left"].beta = smoothing

    def get_ui_data(self):
        grabbed, frame = self.camera.read()
        if not grabbed or frame is None:
            return None, [], 0, "None", False

        frame = cv2.flip(frame, 1)
        curr_time = time.time()

        hands_data = self.engine.process_frame(frame)

        if curr_time - self.last_profile_check > 2.0:
            mode = get_active_app_mode()
            self.current_profile = self.profiles.get(mode, self.profiles["DEFAULT"])
            self.last_profile_check = curr_time

        left_gesture = "UNKNOWN"
        right_gesture = "UNKNOWN"

        if not self.auth.is_authenticated:
            current_gesture = hands_data[0]['gesture'] if hands_data else "UNKNOWN"
            auth_info = self.auth.update(current_gesture)
            self.hud.draw_auth_screen(frame, auth_info)
            if hands_data and auth_info[1] > 0:
                h, w = frame.shape[:2]
                palm = hands_data[0]['landmarks'][0]
                center = (int(palm.x * w), int(palm.y * h))
                self.hud.draw_progress_circle(frame, center, auth_info[1])
        else:
            for hand in hands_data:
                gesture = hand['gesture']
                if hand['hand'] == "Right": right_gesture = gesture
                else: left_gesture = gesture

                action = self.current_profile.get_action(gesture, hand['hand'])
                if action:
                    from gestures.actions import MoveCursorAction
                    if isinstance(action, MoveCursorAction):
                        action.execute(hand['x'], hand['y'])
                    else:
                        action.execute()
            
            if left_gesture != "UNKNOWN" and right_gesture != "UNKNOWN":
                self.global_shortcuts.check(left_gesture, right_gesture)

        self.fps = 1 / (curr_time - self.last_time + 1e-6)
        self.last_time = curr_time
        self.hud.draw(frame, hands_data, self.fps, self.current_profile.name)
        return frame, hands_data, self.fps, self.current_profile.name, self.auth.is_authenticated

    def stop(self):
        self.camera.stop()
        self.engine.close()
