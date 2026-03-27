import math
import random
import numpy as np

class DynamicObject:
    def __init__(self, obj_id, obj_type, x, y, angle=0, speed=0):
        self.id = obj_id
        self.type = obj_type # "pedestrian", "npc_car"
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.alive = True
        self.width = 1.0
        self.length = 1.0

    def get_state(self):
        return {
            "id": self.id,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
            "speed": self.speed,
            "alive": self.alive
        }

    def update(self, dt, simulation=None):
        pass

class Pedestrian(DynamicObject):
    def __init__(self, obj_id, start_node, speed=None):
        self.current_node = start_node
        self.next_node = None
        self.path = []
        self.path_idx = 0
        self.forward = True
        super().__init__(obj_id, "pedestrian", 0, 0, speed=speed if speed is not None else random.uniform(1.0, 1.5))
        self.width = 0.6
        self.length = 0.6

    def _generate_path(self, graph, num_waypoints=5):
        path = [self.current_node]
        curr = self.current_node
        for _ in range(num_waypoints):
            options = [e[1] for e in graph["edges"] if e[0] == curr]
            if not options:
                break
            curr = random.choice(options)
            path.append(curr)
        return path

    def update(self, dt, simulation=None):
        if not self.alive or not simulation: return
        graph = simulation.track.data.get("graph")
        if not graph: return

        if self.x == 0 and self.y == 0:
            pos = graph["nodes"].get(self.current_node)
            if pos: 
                self.x, self.y = pos
                self.path = self._generate_path(graph)
            else: 
                self.alive = False; return

        if not self.next_node:
            if self.forward:
                self.path_idx += 1
                if self.path_idx >= len(self.path):
                    self.forward = False
                    self.path_idx = len(self.path) - 2
            else:
                self.path_idx -= 1
                if self.path_idx < 0:
                    self.forward = True
                    self.path_idx = 1
                    
            if 0 <= self.path_idx < len(self.path):
                self.next_node = self.path[self.path_idx]
            else:
                return

        target = graph["nodes"][self.next_node]
        dx, dy = target[0] - self.x, target[1] - self.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist < 1.0:
            self.current_node = self.next_node
            self.next_node = None
            return

        self.angle = math.atan2(dy, dx)
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

class NPCCar(DynamicObject):
    def __init__(self, obj_id, start_node, speed=None):
        self.current_node = start_node
        self.next_node = None
        self.v_des = speed if speed is not None else random.uniform(5.0, 9.0)
        super().__init__(obj_id, "npc_car", 0, 0, speed=self.v_des)
        self.width = 1.8
        self.length = 4.0
        
        # IDM parameters
        self.a_max = 1.5      # max acceleration
        self.b = 2.0          # comfortable deceleration
        self.s0 = 4.0         # minimum gap
        self.T = 1.5          # safe time headway
        self.delta = 4.0      # acceleration exponent

    def update(self, dt, simulation=None):
        if not self.alive or not simulation: return
        graph = simulation.track.data.get("graph")
        if not graph: return

        if self.x == 0 and self.y == 0:
            pos = graph["nodes"].get(self.current_node)
            if pos: self.x, self.y = pos
            else: self.alive = False; return

        if not self.next_node:
            options = [e[1] for e in graph["edges"] if e[0] == self.current_node]
            if not options:
                options = [e[0] for e in graph["edges"] if e[1] == self.current_node]
            if options:
                self.next_node = random.choice(options)
            else: return

        target = graph["nodes"][self.next_node]
        dx, dy = target[0] - self.x, target[1] - self.y
        dist = math.sqrt(dx**2 + dy**2)

        if dist < 4.0:
            self.current_node = self.next_node
            self.next_node = None
            return

        target_angle = math.atan2(dy, dx)
        angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        self.angle += angle_diff * 5.0 * dt
        
        # Intelligent Driver Model (IDM)
        s_actual = 999.0
        v_lead = self.v_des
        
        # Find closest object ahead
        all_vehicles = simulation.cars + [obj for obj in simulation.dynamic_objects if obj.id != self.id]
        for obj in all_vehicles:
            if not obj.alive: continue
            
            # Simple cone check ahead
            v_dx = obj.x - self.x
            v_dy = obj.y - self.y
            d = math.sqrt(v_dx**2 + v_dy**2)
            if d < 40.0:
                dot = math.cos(self.angle) * v_dx + math.sin(self.angle) * v_dy
                if dot > 0 and dot > d * 0.866: # Within +/- 30 degrees ahead
                    if d < s_actual:
                        s_actual = d
                        # Approximate leading vehicle speed
                        v_lead = getattr(obj, 'speed', 0.0)

        # IDM Calculation
        delta_v = self.speed - v_lead
        s_des = self.s0 + self.speed * self.T + (self.speed * delta_v) / (2 * math.sqrt(self.a_max * self.b))
        
        # Prevent division by zero and constrain acceleration
        s_actual = max(0.1, s_actual)
        
        acceleration = self.a_max * (1.0 - (self.speed / self.v_des)**self.delta - (s_des / s_actual)**2)
        
        # Update speed and position
        self.speed += acceleration * dt
        self.speed = max(0.0, self.speed) # No reverse
        
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt
