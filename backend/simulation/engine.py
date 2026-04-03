import os
import cv2
import csv
import time
import threading
import torch
import numpy as np
from queue import Queue
from backend.simulation.car import Car
from backend.simulation.sensors import Sensors
from backend.simulation.track import Track
from backend.simulation.neural import SimpleFFN, PilotNet
from backend.simulation.genetic import Population
from backend.simulation.objects import Pedestrian, NPCCar
from backend.auto_learning import AutoLearningManager
from backend.simulation.lane_follower import LaneFollower
import math

class SimulationEngine(threading.Thread):
    def __init__(self, sim_id, track_data, state_queue):
        super().__init__()
        self.daemon = True  # Allow clean process exit
        self.sim_id = sim_id
        self.state_queue = state_queue
        self.running = True
        self.paused = False
        
        # Mode: "ga" or "dl" or "pid"
        self.mode = "ga"
        self.recording = False
        self.recording_dir = "backend/data/training"
        self.images_dir = os.path.join(self.recording_dir, "images")
        self.csv_path = os.path.join(self.recording_dir, "driving_log.csv")
        
        # Statistics
        self.collision_stats = {
            "pedestrian_hits": 0,
            "npc_hits": 0,
            "boundary_hits": 0,
            "clean_laps": 0
        }
        
        # Setup environment
        self.track = Track(track_data)
        self.sensors = Sensors()
        
        # GA Setup
        self.pop_size = 50
        self.ga_nn = SimpleFFN()
        self.genome_size = len(self.ga_nn.get_weights())
        self.population = Population(self.pop_size, self.genome_size)
        
        # DL Setup
        self.dl_model = PilotNet()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.dl_model.to(self.device)
        self.dl_model.eval()
        
        # Cars
        self.cars = []
        self.dynamic_objects = []
        track_id = track_data.get("id", "default_track")
        
        try:
            self.auto_learner = AutoLearningManager(track_id=track_id)
        except Exception as e:
            print(f"[!] AutoLearningManager init failed: {e}")
            self.auto_learner = None
        
        self.lane_follower = None
        if "roads" in track_data and len(track_data["roads"]) > 0:
            centerline = track_data["roads"][0].get("points", [])
            if len(centerline) > 1:
                try:
                    self.lane_follower = LaneFollower(centerline)
                except Exception as e:
                    print(f"[!] LaneFollower init failed: {e}")
                
        self._load_dynamic_objects(track_data)
        self.reset_cars()

    def _load_dynamic_objects(self, track_data):
        objs_data = track_data.get("dynamic_objects", [])
        self.dynamic_objects = []
        for i, obj in enumerate(objs_data):
            try:
                if obj["type"] == "pedestrian":
                    self.dynamic_objects.append(Pedestrian(f"p_{i}", obj["start_node"], obj.get("speed")))
                elif obj["type"] == "npc_car":
                    self.dynamic_objects.append(NPCCar(f"npc_{i}", obj["start_node"], obj.get("speed")))
            except Exception as e:
                print(f"[!] Failed to load dynamic object {i}: {e}")

    def reset_cars(self):
        self.cars = []
        # Use track's robust start position extraction
        start_x, start_y, start_angle = self.track.get_start_position()
        
        if self.mode == "ga":
            for _ in range(self.pop_size):
                self.cars.append(Car(start_x, start_y, start_angle))
        else:
            # Single or few cars for DL/PID
            self.cars.append(Car(start_x, start_y, start_angle))

    def stop(self):
        self.running = False

    def run_one_step(self, dt=0.016):
        # Clamp dt to avoid physics explosions
        dt = min(dt, 0.1)
        
        # 1. Update Dynamic Objects
        for obj in self.dynamic_objects:
            try:
                obj.update(dt, self)
            except Exception:
                pass
            
        # 2. Update Cars
        all_dead = True
        recorded_this_step = False
        last_action = [0, 0]  # Track last action for auto-collection
        
        for i, car in enumerate(self.cars):
            if not car.alive: continue
            all_dead = False
            
            # Get Inputs
            try:
                sensor_readings = self.sensors.get_readings(car, self.track, self.dynamic_objects)
            except Exception:
                sensor_readings = np.ones(self.sensors.num_rays) * self.sensors.ray_length
            
            # Get Action
            action = [0, 0]
            if self.mode == "ga":
                try:
                    self.ga_nn.set_weights(self.population.genomes[i].weights)
                    with torch.no_grad():
                        inp = torch.FloatTensor(sensor_readings / 150.0)
                        action = self.ga_nn(inp).numpy()
                except Exception:
                    action = [0, 0.5]
            elif self.mode == "pid":
                if self.lane_follower:
                    speed = getattr(car, 'speed', 5.0) 
                    try:
                        action = self.lane_follower.get_steering_and_throttle(car.x, car.y, car.angle, speed)
                    except Exception:
                        action = [0, 0.5]
                else:
                    action = [0, 0.5]
            else:
                try:
                    view = self.sensors.get_camera_view(car, self.track)
                    view_tensor = torch.FloatTensor(view).permute(2,0,1).unsqueeze(0).to(self.device) / 255.0
                    with torch.no_grad():
                        action = self.dl_model(view_tensor).cpu().squeeze().numpy()
                except Exception:
                    action = [0, 0.5]
            
            last_action = action
            
            # Update Physics
            car.update(action, dt)
            
            # Record Data (for behavioral cloning)
            if self.recording and self.mode == "ga" and car.alive and not recorded_this_step:
                try:
                    self.save_frame(car, action)
                    recorded_this_step = True
                except Exception as e:
                    print(f"[!] Recording failed: {e}")
            
            # Check Collision (Track)
            if self.track.check_collision(car.get_bbox()):
                car.alive = False
                car.collisions += 1
                self.collision_stats["boundary_hits"] += 1
            
            # Check Collision (Dynamic Objects)
            for obj in self.dynamic_objects:
                if obj.alive:
                    dist = math.sqrt((car.x - obj.x)**2 + (car.y - obj.y)**2)
                    if dist < (car.width/2 + obj.width/2):
                        car.alive = False
                        car.collisions += 1
                        car.fitness -= 200  # Collision penalty
                        if obj.type == "pedestrian":
                            self.collision_stats["pedestrian_hits"] += 1
                        else:
                            self.collision_stats["npc_hits"] += 1
                
            self.track.update_checkpoints(car)
            
            # Update Fitness
            if self.mode == "ga":
                car.fitness = car.last_checkpoint * 100 + car.distance_traveled / 10.0
                if i < len(self.population.genomes):
                    self.population.genomes[i].fitness = car.fitness

        # Auto-collection from the best alive car
        if self.auto_learner and self.mode == "ga":
            try:
                alive_cars = [c for c in self.cars if c.alive]
                if alive_cars:
                    best_car = max(alive_cars, key=lambda x: x.fitness)
                    if best_car.collisions == 0:
                        view = self.sensors.get_camera_view(best_car, self.track)
                        self.auto_learner.add_data(view, last_action[0], last_action[1], best_car.fitness/1000.0, best_car.collisions)
            except Exception:
                pass
        
        # Periodic check for training
        if self.auto_learner:
            try:
                self.auto_learner.check_and_trigger_training()
            except Exception:
                pass

        return all_dead

    def save_frame(self, car, action):
        """Saves camera view and labels (steering/throttle) to the training directory."""
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir, exist_ok=True)
            
        # Ensure CSV header exists
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["image_path", "steering", "throttle", "timestamp"])

        # Capture View
        view = self.sensors.get_camera_view(car, self.track)
        timestamp = int(time.time() * 1000)
        img_name = f"frame_{timestamp}.jpg"
        img_path = os.path.join(self.images_dir, img_name)
        
        cv2.imwrite(img_path, view)
        
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([img_name, action[0], action[1], timestamp])

    def run(self):
        print(f"[*] Engine thread started for simulation {self.sim_id}")
        last_time = time.time()
        
        # Initial state broadcast
        self.broadcast_state()
        
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
                
            now = time.time()
            dt = now - last_time
            last_time = now
            
            if not self.cars:
                self.reset_cars()
                
            all_dead = self.run_one_step(dt)
            
            # Evolution logic
            if all_dead and self.mode == "ga":
                self.population.evolve()
                self.reset_cars()
            elif all_dead and (self.mode == "dl" or self.mode == "pid"):
                self.reset_cars()
                
            self.broadcast_state()
            time.sleep(0.016)

    def broadcast_state(self):
        # Get track bounds for frontend camera
        bounds = self.track.get_bounds()
        
        state = {
            "sim_id": self.sim_id,
            "generation": self.population.generation if self.mode == "ga" else 0,
            "mode": self.mode,
            "timestamp": time.time(),
            "track_bounds": {
                "min_x": bounds[0],
                "min_y": bounds[1],
                "max_x": bounds[2],
                "max_y": bounds[3]
            },
            "cars": [
                {
                    "x": c.x, "y": c.y, "angle": c.angle, 
                    "alive": c.alive, "fitness": c.fitness,
                    "sensors": self._safe_get_sensors(c)
                } for c in self.cars
            ],
            "dynamic_objects": [obj.get_state() for obj in self.dynamic_objects if obj.alive],
            "stats": self.collision_stats,
            "auto_learning": self.auto_learner.get_status() if self.auto_learner else {"is_training": False, "data_count": 0, "last_train": None}
        }
        try:
            self.state_queue.put_nowait(state)
        except:
            pass
    
    def _safe_get_sensors(self, car):
        """Safely get sensor readings without crashing the broadcast."""
        try:
            return self.sensors.get_readings(car, self.track, self.dynamic_objects).tolist()
        except Exception:
            return [150.0] * self.sensors.num_rays
