class PointFilter:
    def __init__(self, alpha=0.1, beta=0.01):
        self.alpha = alpha
        self.beta = beta
        self.prev_raw = None
        self.prev_filtered = None

    def apply(self, x, y):
        current_raw = (x, y)
        if self.prev_raw is None:
            self.prev_raw = current_raw
            self.prev_filtered = current_raw
            return current_raw

        dx = x - self.prev_raw[0]
        dy = y - self.prev_raw[1]
        
        speed = (dx**2 + dy**2)**0.5
        
        adaptive_alpha = self.alpha + self.beta * speed
        adaptive_alpha = min(1.0, adaptive_alpha)

        fx = self.prev_filtered[0] + adaptive_alpha * (x - self.prev_filtered[0])
        fy = self.prev_filtered[1] + adaptive_alpha * (y - self.prev_filtered[1])
        
        self.prev_raw = current_raw
        self.prev_filtered = (fx, fy)
        
        return fx, fy
