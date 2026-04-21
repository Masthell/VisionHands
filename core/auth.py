import time

class AuthSystem:
    def __init__(self):
        self.password = ["POINTER", "OK_SIGN", "PEACE", "FIST"]
        self.current_step = 0
        self.is_authenticated = False
        self.hold_start_time = None
        self.hold_duration = 1.5

    def update(self, current_gesture):
        if self.is_authenticated:
            return True, 0

        target_gesture = self.password[self.current_step]

        if current_gesture == target_gesture:
            if self.hold_start_time is None:
                self.hold_start_time = time.time()
            
            elapsed = time.time() - self.hold_start_time
            if elapsed >= self.hold_duration:
                self.current_step += 1
                self.hold_start_time = None
                if self.current_step >= len(self.password):
                    self.is_authenticated = True
            return False, elapsed / self.hold_duration
        else:
            self.hold_start_time = None
            return False, 0
