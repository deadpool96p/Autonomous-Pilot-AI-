import json
from shapely.geometry import Polygon, LineString, MultiLineString, Point

class Track:
    def __init__(self, track_data):
        self.data = track_data
        self.polygons = []
        self.boundaries = None
        self.checkpoints = []
        self.bounds = None  # (min_x, min_y, max_x, max_y)
        
        self.load_from_data(track_data)

    def load_from_data(self, data):
        # Road segments/polygons
        for road in data.get("roads", []):
            try:
                if "width" in road:
                    # Centerline + width (Common in OSM import)
                    if len(road["points"]) < 2: continue
                    line = LineString(road["points"])
                    poly = line.buffer(road["width"] / 2)
                    self.polygons.append(poly)
                elif len(road["points"]) >= 3:
                    # Direct polygon points (Legacy format)
                    poly = Polygon(road["points"])
                    if poly.is_valid:
                        self.polygons.append(poly)
            except Exception as e:
                print(f"[!] Warning: Failed to process road segment: {e}")
                continue
            
        # Extract boundaries for ray-casting
        lines = []
        for poly in self.polygons:
            lines.append(poly.exterior)
        if lines:
            self.boundaries = MultiLineString(lines)
        else:
            self.boundaries = MultiLineString([])
            
        # Calculate overall bounds
        self._calculate_bounds()
            
        # Checkpoints
        for cp in data.get("checkpoints", []):
            try:
                if isinstance(cp, list):  # [x, y] point
                    p = Point(cp)
                    self.checkpoints.append(p.buffer(5).exterior)
                elif "points" in cp:
                    self.checkpoints.append(LineString(cp["points"]))
            except Exception as e:
                print(f"[!] Warning: Failed to process checkpoint: {e}")
                continue

    def _calculate_bounds(self):
        """Calculate the overall bounding box of all road polygons."""
        if not self.polygons:
            self.bounds = (0, 0, 1000, 800)
            return
            
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for poly in self.polygons:
            b = poly.bounds  # (minx, miny, maxx, maxy)
            min_x = min(min_x, b[0])
            min_y = min(min_y, b[1])
            max_x = max(max_x, b[2])
            max_y = max(max_y, b[3])
        
        self.bounds = (min_x, min_y, max_x, max_y)

    def get_bounds(self):
        """Returns (min_x, min_y, max_x, max_y) of the track."""
        if self.bounds is None:
            self._calculate_bounds()
        return self.bounds

    def get_start_position(self):
        """
        Returns a valid starting position (x, y, angle) for cars.
        Uses track data's start_pos/start_angle if available,
        otherwise uses the first road's starting point.
        """
        # Check for explicit start position
        if "start_pos" in self.data:
            pos = self.data["start_pos"]
            angle = self.data.get("start_angle", 0)
            return pos[0], pos[1], angle
        
        # Fallback: use the first road's first point
        roads = self.data.get("roads", [])
        if roads and "points" in roads[0] and len(roads[0]["points"]) >= 2:
            p0 = roads[0]["points"][0]
            p1 = roads[0]["points"][1]
            import math
            angle = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            return p0[0], p0[1], angle
        
        # Absolute fallback
        return 200, 300, 0

    def check_collision(self, car_bbox):
        """Checks if the car bounding box is outside all roads or inside any obstacle."""
        if not self.polygons:
            return False  # No roads defined, don't kill cars
            
        car_poly = Polygon(car_bbox)
        
        # Check if car is inside any road polygon
        inside_road = False
        for poly in self.polygons:
            if poly.contains(car_poly) or poly.intersects(car_poly):
                inside_road = True
                break
        
        # Collision if NOT inside any road
        return not inside_road

    def update_checkpoints(self, car):
        """Checks if car passed a new checkpoint and returns number of checkpoints passed."""
        if not self.checkpoints:
            return car.last_checkpoint
            
        next_cp_idx = (car.last_checkpoint + 1)
        if next_cp_idx >= len(self.checkpoints):
            # Wrap around for laps
            return car.last_checkpoint
            
        cp_line = self.checkpoints[next_cp_idx]
        car_pos = Point(car.x, car.y)
        
        # Simple proximity-based detection
        if car_pos.distance(cp_line) < 10.0:
            car.last_checkpoint = next_cp_idx
            
        return car.last_checkpoint
