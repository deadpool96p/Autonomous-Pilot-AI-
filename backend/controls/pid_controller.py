class PIDController:
    def __init__(self, kp=0.8, ki=0.01, kd=0.1):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0.0
        self.last_error = 0.0

    def compute(self, error, dt=0.033):
        if dt <= 0.0:
            dt = 0.033
        self.integral += error * dt
        derivative = (error - self.last_error) / dt
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.last_error = error
        return max(-1.0, min(1.0, output))

    def reset(self):
        self.integral = 0.0
        self.last_error = 0.0
