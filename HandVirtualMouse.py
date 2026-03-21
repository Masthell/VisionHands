import cv2
import numpy as np
import HandTrackingModule as htm
import time
import json
import os
from pynput.mouse import Button, Controller

class NeuroBrain:
    """Простая самообучающаяся надстройка"""
    def __init__(self):
        self.log_file = "hand_experience.json"
        self.data = self.load_data()
        # Начальные параметры, которые будут меняться
        self.click_threshold = self.data.get("avg_click_dist", 35)
        self.move_count = 0
        self.session_distances = []

    def load_data(self):
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                return json.load(f)
        return {}

    def learn_click(self, dist):
        """Обучается на расстоянии между пальцами при клике"""
        self.session_distances.append(dist)
        if len(self.session_distances) > 50:
            new_avg = sum(self.session_distances) / len(self.session_distances)
            self.click_threshold = (self.click_threshold + new_avg) / 2
            self.save_experience()
            self.session_distances = []

    def save_experience(self):
        with open(self.log_file, "w") as f:
            json.dump({"avg_click_dist": self.click_threshold}, f)

# Инициализация
brain = NeuroBrain()
mouse = Controller()
cap = cv2.VideoCapture(0)
detector = htm.handDetector(detectionCon=0.8, maxHands=1)

p_loc_x, p_loc_y = 0, 0
SMOOTHING = 5 

while True:
    success, img = cap.read()
    if not success: break
    img = cv2.flip(img, 1)
    img = detector.findHands(img, draw=True)
    lmList = detector.findPosition(img, draw=False)

    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]
        fingers = detector.fingersUp()

        # ДВИЖЕНИЕ
        if fingers[1] == 1 and fingers[2] == 0:
            # Используем динамическую рамку (можно тоже обучать)
            x3 = np.interp(x1, (100, 540), (0, 1920))
            y3 = np.interp(y1, (100, 380), (0, 1080))
            
            curr_x = p_loc_x + (x3 - p_loc_x) / SMOOTHING
            curr_y = p_loc_y + (y3 - p_loc_y) / SMOOTHING
            mouse.position = (int(curr_x), int(curr_y))
            p_loc_x, p_loc_y = curr_x, curr_y

        # КЛИК С ОБУЧЕНИЕМ
        if fingers[1] == 1 and fingers[2] == 1:
            dist = np.hypot(x2 - x1, y2 - y1)
            
            # Система использует порог, который она выучила сама!
            if dist < brain.click_threshold + 5: 
                mouse.click(Button.left, 1)
                brain.learn_click(dist) # "Запоминаем", на каком расстоянии был клик
                
                cv2.putText(img, f"Smart Click: {int(dist)}px", (x1, y1-20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                time.sleep(0.15)

    # Вывод текущего "интеллекта" системы
    cv2.putText(img, f"AI Threshold: {int(brain.click_threshold)}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

    cv2.imshow("AI Hand Mouse", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()