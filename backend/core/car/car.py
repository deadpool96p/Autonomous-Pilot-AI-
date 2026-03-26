import pygame
import math
import numpy as np
from backend.core.config import SENSOR_COUNT, SENSOR_LENGTH, WHEELBASE, DRAG_COEFFICIENT, MAX_SPEED

class Car:
    def __init__(self, x, y, angle, genome):
        self.pos = pygame.Vector2(x, y)
        self.angle = angle
        self.speed = 0
        self.genome = genome
        self.alive = True
        self.distance = 0
        self.time_alive = 0
        self.sensors = [0] * SENSOR_COUNT
        self.collided = False
        self.last_checkpoint = -1

    def get_inputs(self):
        # Normalize sensors for the AI (0 to 1)
        return np.array(self.sensors) / SENSOR_LENGTH

    def update(self, action, dt=1.0):
        if not self.alive: return
        
        # Action[0] = Steering Angle (-1 to 1) -> maps to degrees
        # Action[1] = Acceleration (-1 to 1)
        steering_angle = action[0] * 30 # Max 30 degrees
        acceleration = action[1] * 0.5
        
        # Bicycle Model Kinematics
        rad = math.radians(self.angle)
        self.pos.x += self.speed * math.cos(rad) * dt
        self.pos.y -= self.speed * math.sin(rad) * dt
        
        self.angle += (self.speed / WHEELBASE) * math.tan(math.radians(steering_angle)) * dt * (180/math.pi)
        
        self.speed += acceleration * dt
        self.speed -= DRAG_COEFFICIENT * self.speed * dt
        self.speed = max(0, min(self.speed, MAX_SPEED))
        
        self.distance += self.speed * dt
        self.time_alive += 1

    def draw(self, screen):
        color = (0, 255, 0) if self.alive else (200, 0, 0)
        
        # 1. Draw Sensor Rays (Only for the living)
        if self.alive:
            start_angle = self.angle - 45
            step = 90 / (len(self.sensors) - 1)
            for i, dist in enumerate(self.sensors):
                angle = math.radians(start_angle + (i * step))
                end_x = self.pos.x + math.cos(angle) * dist
                end_y = self.pos.y - math.sin(angle) * dist
                pygame.draw.line(screen, (100, 100, 100), (self.pos.x, self.pos.y), (end_x, end_y), 1)

        # 2. Draw Car Body (Rotated Rectangle representation)
        surface = pygame.Surface((30, 15), pygame.SRCALPHA)
        pygame.draw.rect(surface, color, (0, 0, 30, 15))
        rotated_surface = pygame.transform.rotate(surface, self.angle)
        rect = rotated_surface.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        screen.blit(rotated_surface, rect)