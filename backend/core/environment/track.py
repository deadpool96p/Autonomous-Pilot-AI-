import pygame
import json
from shapely.geometry import Polygon, Point, LineString
from backend.core.config import SCREEN_WIDTH, SCREEN_HEIGHT, TRACK_FILE

class Track:
    def __init__(self, track_file=TRACK_FILE):
        self.load_track(track_file)
        try:
            self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.create_visuals()
        except Exception:
            self.surface = None
            self.mask = None
        
    def load_track(self, track_input):
        if isinstance(track_input, dict):
            data = track_input
        else:
            with open(track_input, "r") as f:
                data = json.load(f)
            
        self.name = data.get("name", "Unnamed Track")
        self.spawn_point = data["spawn_point"]
        
        # Road boundaries as shapely Polygons
        self.road_polygons = [Polygon(p) for p in data["road_boundaries"]]
        
        # Obstacles as shapely Polygons
        self.obstacle_polygons = []
        for obs in data.get("obstacles", []):
            self.obstacle_polygons.append(Polygon(obs["points"]))
            
        # Checkpoints as shapely LineStrings
        self.checkpoints = [LineString([c["start"], c["end"]]) for c in data.get("checkpoints", [])]
        
        # Mask for backward compatibility with ray-casting if needed, 
        # but we'll try to use shapely for sensors too
        self.mask = None 

    def create_visuals(self):
        self.surface.fill((30, 30, 30))
        # Draw road boundaries
        for poly in self.road_polygons:
            points = list(poly.exterior.coords)
            pygame.draw.polygon(self.surface, (80, 80, 80), points)
        
        # Punch holes for infields (if any) - this is a bit tricky with simple polygons
        # For simplicity, we assume the first boundary is outer and others are holes
        if len(self.road_polygons) > 1:
            for poly in self.road_polygons[1:]:
                points = list(poly.exterior.coords)
                pygame.draw.polygon(self.surface, (30, 30, 30), points)

        # Draw obstacles
        for poly in self.obstacle_polygons:
            points = list(poly.exterior.coords)
            pygame.draw.polygon(self.surface, (255, 0, 0), points)

        self.mask = pygame.mask.from_threshold(self.surface, (80, 80, 80), (1, 1, 1))

    def is_colliding(self, car_pos):
        point = Point(car_pos.x, car_pos.y)
        
        # Must be WITHIN the first polygon (outer road boundary)
        if not self.road_polygons[0].contains(point):
            return True
            
        # Must NOT be WITHIN any subsequent road polygons (holes/infields)
        if len(self.road_polygons) > 1:
            for hole in self.road_polygons[1:]:
                if hole.contains(point):
                    return True
                    
        # Must NOT hit any obstacles
        for obs in self.obstacle_polygons:
            if obs.contains(point):
                return True
                
        return False

    def draw(self, screen):
        screen.blit(self.surface, (0, 0))
            
