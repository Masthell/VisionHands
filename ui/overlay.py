import cv2
import numpy as np

class HUD:
    def __init__(self):
        self.color_main = (255, 90, 0) # Основа (Синий)
        self.color_acc = (255, 200, 0) # Акцент (Голубой)
        # ИСПРАВЛЕНИЕ: устанавливаем правильные BGR цвета для синего стиля
        self.color_main = (255, 90, 0) 
        self.color_acc = (255, 170, 0)

    def draw(self, frame, hands_data, fps, profile_name):
        h, w = frame.shape[:2]
        
        cv2.putText(frame, f"FPS: {int(fps)}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
        cv2.putText(frame, f"MODE: {profile_name}", (20, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)

        for hand in hands_data:
            landmarks = hand['landmarks']
            for lm in landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 3, (255, 90, 0), -1) # Синие точки
            
            p8 = landmarks[8]
            cv2.circle(frame, (int(p8.x * w), int(p8.y * h)), 10, (255, 200, 0), 2)
            cv2.putText(frame, hand['gesture'], (int(landmarks[0].x * w), int(landmarks[0].y * h) - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def draw_auth_screen(self, frame, auth_info):
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (15, 5, 5), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        text = "GESTURE AUTHENTICATION"
        cv2.putText(frame, text, (w//2 - 160, h//2 - 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 120, 0), 2)

    def draw_progress_circle(self, frame, center, progress):
        cv2.ellipse(frame, center, (40, 40), 0, 0, progress * 360, (0, 255, 0), 5)
