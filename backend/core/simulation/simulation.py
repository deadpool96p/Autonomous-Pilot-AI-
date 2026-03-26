import pygame
import sys
import pickle
from backend.core.config import *
from backend.core.car.car import Car
from backend.core.ai.neural_network import NeuralNetwork
from backend.core.genetic.population import Genome, evolve
from backend.core.environment.track import Track
from backend.core.car.sensors import Sensors
from backend.core.simulation.recorder import DataRecorder
from shapely.geometry import Point, LineString

class Simulation:
    def __init__(self, headless=False, track_file=TRACK_FILE):
        self.headless = headless
        if not self.headless:
            try:
                pygame.init()
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                pygame.display.set_caption("AI Self-Driving Simulation")
                self.clock = pygame.time.Clock()
                pygame.font.init()
                self.font = pygame.font.SysFont("Arial", 18)
                
                # Button Rects
                self.stop_btn = pygame.Rect(SCREEN_WIDTH - 120, 10, 100, 40)
                self.load_btn = pygame.Rect(SCREEN_WIDTH - 230, 10, 100, 40)
            except Exception:
                self.headless = True
        
        self.track = Track(track_file)
        self.nn = NeuralNetwork()
        self.sensor_system = Sensors(SENSOR_COUNT)
        
        self.generation = 1
        self.paused = False
        self.mode = "ga" # "ga", "dl", "manual"
        self.recording = False
        self.recorder = DataRecorder()
        self.dl_model = None # To be loaded during DL mode
        
        self.population = [Genome() for _ in range(POPULATION_SIZE)]
        self.reset_env()

    def reset_env(self):
        # Use track-specific spawn point
        sx = self.track.spawn_point.get("x", SPAWN_X)
        sy = self.track.spawn_point.get("y", SPAWN_Y)
        sa = self.track.spawn_point.get("angle", SPAWN_ANGLE)
        self.cars = [Car(sx, sy, sa, g) for g in self.population]

    def run(self):
        """Main Loop: Headless or Pygame."""
        if self.headless:
            while True:
                self.update()
        else:
            while True:
                self.handle_events()
                if not self.paused:
                    # In manual mode, we might wait for input here or sample at FPS
                    self.update()
                self.draw()
                self.clock.tick(FPS)

    def handle_events(self):
        if self.headless: return
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_best_and_quit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.recording = not self.recording
                    if self.recording: self.recorder.start_session()
                    else: self.recorder.stop_session()
                
                if event.key == pygame.K_m:
                    modes = ["ga", "dl", "manual"]
                    curr_idx = modes.index(self.mode)
                    self.mode = modes[(curr_idx + 1) % len(modes)]
                    print(f"[SIM] Switched to mode: {self.mode}")
                    self.reset_env()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.stop_btn.collidepoint(event.pos):
                    self.paused = not self.paused
                
                if self.load_btn.collidepoint(event.pos):
                    from backend.core.genetic.population import load_best_genome, create_population_from_saved
                    saved = load_best_genome()
                    if saved:
                        self.population = create_population_from_saved(saved)
                        self.generation = "Loaded"
                        self.reset_env()

    def update(self):
        alive_count = 0
        from backend.core.simulation.fitness import calculate_fitness
        
        # Manual Input Sampling
        manual_action = [0, 0]
        if self.mode == "manual" and not self.headless:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]: manual_action[0] = -1
            if keys[pygame.K_RIGHT]: manual_action[0] = 1
            if keys[pygame.K_UP]: manual_action[1] = 1
            if keys[pygame.K_DOWN]: manual_action[1] = -1

        for car in self.cars:
            if car.alive:
                # 1. Update sensors
                car.sensors = self.sensor_system.get_readings(
                    car.pos, car.angle, self.track
                )
                
                # 2. Get Action based on mode
                if self.mode == "ga":
                    inputs = car.get_inputs()
                    action = self.nn.predict(inputs, car.genome.weights)
                elif self.mode == "dl" and self.dl_model:
                    # To be implemented when model is ready
                    inputs = car.get_inputs()
                    import torch
                    with torch.no_grad():
                        action = self.dl_model(torch.FloatTensor(inputs)).numpy()
                elif self.mode == "manual":
                    action = manual_action
                else:
                    action = [0, 0] # Default
                
                # 3. Move car
                prev_pos = Point(car.pos.x, car.pos.y)
                car.update(action)
                curr_pos = Point(car.pos.x, car.pos.y)
                movement_line = LineString([prev_pos, curr_pos])

                # 4. Checkpoint crossing
                next_checkpoint_idx = car.last_checkpoint + 1
                if next_checkpoint_idx < len(self.track.checkpoints):
                    checkpoint = self.track.checkpoints[next_checkpoint_idx]
                    if movement_line.intersects(checkpoint):
                        car.last_checkpoint = next_checkpoint_idx

                # 5. Collision check
                if self.track.is_colliding(car.pos):
                    car.alive = False
                    car.collided = True
                    car.genome.fitness = calculate_fitness(car)
                
                # 6. Record Data (Only for the first car in manual/GA champion mode for clarity)
                if self.recording and (self.mode == "manual" or car == self.cars[0]):
                    self.recorder.record(car.sensors, car.speed, action[0], action[1])
                
                alive_count += 1

        if alive_count == 0 and self.mode == "ga":
            self.population = evolve(self.population)
            self.generation += 1
            self.reset_env()
        elif alive_count == 0:
            self.reset_env() # Just respawn in DL/Manual mode

    def draw(self):
        if self.headless: return
        self.track.draw(self.screen)
        for car in self.cars:
            car.draw(self.screen)

        # Draw Buttons
        pygame.draw.rect(self.screen, (200, 50, 50) if not self.paused else (50, 200, 50), self.stop_btn)
        pygame.draw.rect(self.screen, (50, 50, 200), self.load_btn) # Blue Load Button
        
        self.screen.blit(self.font.render("STOP" if not self.paused else "START", True, (255,255,255)), (self.stop_btn.x + 25, self.stop_btn.y + 10))
        self.screen.blit(self.font.render("LOAD", True, (255,255,255)), (self.load_btn.x + 25, self.load_btn.y + 10))
        
        # Stats
        stats = self.font.render(f"Gen: {self.generation} | Alive: {sum(1 for c in self.cars if c.alive)}", True, (255, 255, 255))
        self.screen.blit(stats, (10, 10))
        
        pygame.display.flip()

    def save_best_and_quit(self):
        # Save the best performing genome before closing
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        with open("saved_genome.pkl", "wb") as f:
            pickle.dump(self.population[0], f)
        pygame.quit()
        sys.exit()