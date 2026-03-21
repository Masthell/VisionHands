import cv2
import mediapipe as mp
import math

class handDetector():
    def __init__(self, mode=False, maxHands=1, modelComplexity=0, 
                 detectionCon=0.7, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.modelComplex = modelComplexity
        
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            model_complexity=self.modelComplex,
            min_detection_confidence=detectionCon,
            min_tracking_confidence=trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils
        
        self.tipIds = [4, 8, 12, 16, 20]
        self.pipIds = [3, 6, 10, 14, 18]

    def findHands(self, img, draw=False):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        return img
            
    def findPosition(self, img, handNo=0, draw=False):
        self.lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            h, w, c = img.shape
            
            for id, lm in enumerate(myHand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])
                
        return self.lmList
    
    def fingersUp(self):
        if len(self.lmList) == 0:
            return [0, 0, 0, 0, 0]
        
        fingers = []
        
        # Большой палец
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0]-1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        
        # Остальные пальцы
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.pipIds[id]][2]:
                fingers.append(1)
            else:
                fingers.append(0)
                
        return fingers
    
    def findDistance(self, p1, p2, img, draw=False):
        if len(self.lmList) > max(p1, p2):
            x1, y1 = self.lmList[p1][1:]
            x2, y2 = self.lmList[p2][1:]
            length = math.hypot(x2 - x1, y2 - y1)

            if draw:
                cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
                
            return length, img, [x1, y1, x2, y2]
        
        return 100, img, [0, 0, 0, 0]