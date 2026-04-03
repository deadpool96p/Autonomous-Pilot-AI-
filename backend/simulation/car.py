import math
import numpy as np

class Car:
    def __init__(self, x=0, y=0, angle=0):
        # Physical parameters
        self.wheelbase = 2.5 # meters
        self.mass = 1200.0   # kg
        self.drag = 0.05     # Simplified drag coefficient
        self.max_speed = 40.0 # m/s (approx 144 km/h)
        self.steering_range = math.radians(35) # 35 degrees
        
        # State
        self.x = x
        self.y = y
        self.angle = angle # radians
        self.speed = 0.0
        
        # Dimensions for collision
        self.width = 1.8
        self.length = 4.0
        
        # Tracking
        self.alive = True
        self.distance_traveled = 0.0
        self.last_checkpoint = -1
        self.time_alive = 0.0
        self.fitness = 0.0
        self.collisions = 0

    def update(self, action, dt=0.016):
        """
        Update car state using bicycle model.
        action: [steering (-1 to 1), throttle (-1 to 1)]
        """
        if not self.alive:
            return

        steering = action[0] * self.steering_range
        throttle = action[1]
        
        # Simple acceleration model
        acceleration = throttle * 5.0 # m/s^2
        
        # Update speed with drag
        self.speed += (acceleration - self.drag * self.speed) * dt
        self.speed = max(0, min(self.speed, self.max_speed))
        
        # Bicycle model equations
        # x += v * cos(θ) * dt
        # y += v * sin(θ) * dt
        # θ += (v / wheelbase) * tan(δ) * dt
        
        self.x += self.speed * math.cos(self.angle) * dt
        self.y += self.speed * math.sin(self.angle) * dt
        self.angle += (self.speed / self.wheelbase) * math.tan(steering) * dt
        
        self.distance_traveled += self.speed * dt
        self.time_alive += dt

    def get_bbox(self):
        """Returns the 4 corners of the car's bounding box."""
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        
        half_l = self.length / 2
        half_w = self.width / 2
        
        corners = [
            (self.x + half_l * cos_a - half_w * sin_a, self.y + half_l * sin_a + half_w * cos_a),
            (self.x + half_l * cos_a + half_w * sin_a, self.y + half_l * sin_a - half_w * cos_a),
            (self.x - half_l * cos_a + half_w * sin_a, self.y - half_l * sin_a - half_w * cos_a),
            (self.x - half_l * cos_a - half_w * sin_a, self.y - half_l * sin_a + half_w * cos_a)
        ]
        return corners
