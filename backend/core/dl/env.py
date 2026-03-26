import gymnasium as gym
from gymnasium import spaces
import numpy as np
from backend.core.simulation.simulation import Simulation

class DrivingEnv(gym.Env):
    def __init__(self, track_file=None):
        super(DrivingEnv, self).__init__()
        # 5 sensors as input
        self.observation_space = spaces.Box(low=0, high=1, shape=(5,), dtype=np.float32)
        # Steering (-1, 1), Throttle (-1, 1)
        self.action_space = spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32)
        
        self.sim = Simulation(headless=True, track_file=track_file)
        self.car = self.sim.cars[0] # Single car for training

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.sim.reset_env()
        self.car = self.sim.cars[0]
        obs = np.array(self.car.sensors) / 150.0
        return obs.astype(np.float32), {}

    def step(self, action):
        # 1. Update simulation with agent action
        self.car.update(action)
        
        # 2. Get observation
        self.car.sensors = self.sim.sensor_system.get_readings(
            self.car.pos, self.car.angle, self.sim.track
        )
        obs = np.array(self.car.sensors) / 150.0
        
        # 3. Calculate Reward
        # Progress based on checkpoints
        reward = self.car.last_checkpoint * 10
        # Speed bonus
        reward += self.car.speed * 0.1
        
        # 4. Check if Done
        terminated = False
        if self.sim.track.is_colliding(self.car.pos):
            terminated = True
            reward -= 50 # Penalty for crash
        
        truncated = self.car.time_alive > 1000 # Timeout
        
        return obs.astype(np.float32), reward, terminated, truncated, {}

    def render(self):
        pass
