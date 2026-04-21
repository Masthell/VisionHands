import numpy as np

class GestureDetector:
    @staticmethod
    def classify(landmarks, fingers, handedness):
        thumb, index, middle, ring, pinky = fingers

        p4 = np.array([landmarks[4].x, landmarks[4].y])
        p8 = np.array([landmarks[8].x, landmarks[8].y])
        dist = np.linalg.norm(p4 - p8)
        
        if dist < 0.05 and middle and ring and pinky:
            return "OK_SIGN"

        if not thumb and index and middle and ring and pinky:
            return "FOUR"

        if index and not any([middle, ring, pinky]):
            return "POINTER"

        if index and middle and not any([ring, pinky]):
            return "PEACE"

        if not any([index, middle, ring, pinky]):
            return "FIST"

        return "UNKNOWN"
