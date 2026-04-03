import math
from shapely.geometry import Point, LineString
from backend.planning.frenet import FrenetPath
from backend.controls.pid_controller import PIDController

class LaneFollower:
    def __init__(self, track_line, lookahead_base=2.0, kp=0.8, ki=0.01, kd=0.1):
        """
        track_line: List of [x,y] points representing the center of the lane
        """
        self.frenet = FrenetPath(track_line)
        self.pid = PIDController(kp=kp, ki=ki, kd=kd)
        self.lookahead_base = lookahead_base
        
    def get_steering_and_throttle(self, x, y, yaw, speed, target_speed=5.0):
        """
        Compute control action based on vehicle state.
        Returns: (steering, throttle)
        """
        # Lookahead distance proportional to speed
        lookahead = max(self.lookahead_base, speed * 1.0)
        
        # Predictive point
        px = x + math.cos(yaw) * lookahead
        py = y + math.sin(yaw) * lookahead
        
        # Calculate lateral offset at the prediction point
        s, d = self.frenet.get_frenet(px, py)
        
        # The cross-track error is simply 'd'
        error = d 
        
        # PID control for steering (if error > 0, means we are to the left, so steer right?)
        # Frenet convention: left > 0. So if d > 0, we need to steer right (negative steering)
        # We will feed -error to PID so it pulls us back to centerline (d=0).
        steering = self.pid.compute(-error)
        
        # Simple throttle control based on speed
        throttle = 1.0 if speed < target_speed else 0.0
        
        # Slow down on tight curves
        # Check angle of trajectory ahead
        s_ahead = min(s + 10.0, self.frenet.line.length)
        _, _, ahead_yaw = self.frenet.get_cartesian(s_ahead, 0)
        
        yaw_diff = abs((ahead_yaw - yaw + math.pi) % (2 * math.pi) - math.pi)
        if yaw_diff > 0.5:
             throttle = 0.5 if speed < target_speed * 0.5 else 0.0
             
        return steering, throttle
