import math
import numpy as np
from shapely.geometry import LineString, Point

class Sensors:
    def __init__(self, num_rays=7, ray_length=150, spread=math.radians(160)):
        self.num_rays = num_rays
        self.ray_length = ray_length
        self.spread = spread # Total arc of sensors

    def get_readings(self, car, track, dynamic_objects=[]):
        """Returns distances to nearest track boundary or dynamic object for each ray."""
        readings = []
        start_angle = -self.spread / 2
        step = self.spread / (self.num_rays - 1) if self.num_rays > 1 else 0
        
        # Build list of active obstacles nearby
        nearby_obstacles = [track.boundaries]
        for obj in dynamic_objects:
            if obj.alive:
                dist_to_obj = math.sqrt((car.x - obj.x)**2 + (car.y - obj.y)**2)
                if dist_to_obj < self.ray_length + 5.0:
                    # Treat object as a point for simple intersection, or a small buffer
                    nearby_obstacles.append(Point(obj.x, obj.y).buffer(max(obj.width, obj.length)/2).exterior)
        
        for i in range(self.num_rays):
            angle = car.angle + start_angle + i * step
            dx = math.cos(angle) * self.ray_length
            dy = math.sin(angle) * self.ray_length
            
            ray_line = LineString([(car.x, car.y), (car.x + dx, car.y + dy)])
            
            min_dist = self.ray_length
            for obs in nearby_obstacles:
                intersection = obs.intersection(ray_line)
                if not intersection.is_empty:
                    if intersection.geom_type == 'Point':
                        d = Point(car.x, car.y).distance(intersection)
                        min_dist = min(min_dist, d)
                    elif intersection.geom_type == 'MultiPoint':
                        d = min([Point(car.x, car.y).distance(p) for p in intersection.geoms])
                        min_dist = min(min_dist, d)
            
            readings.append(min_dist)
            
        return np.array(readings)

    def get_camera_view(self, car, track, width=200, height=66):
        """
        Synthesizes a simple top-down/perspective view of the road.
        In this simplified version, we'll draw the track boundaries onto a small image buffer.
        """
        import cv2
        # Create a black image
        template = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Center of the "camera" image corresponds to car position
        # We transform track points relative to car's position and angle
        cos_a = math.cos(-car.angle)
        sin_a = math.sin(-car.angle)
        
        # Scale factor for visualization
        scale = 2.0
        
        # Extract track points near the car
        for poly in track.polygons:
            pts = np.array(poly.exterior.coords) - np.array([car.x, car.y])
            # Rotate
            rotated_pts = np.zeros_like(pts)
            rotated_pts[:, 0] = pts[:, 0] * cos_a - pts[:, 1] * sin_a
            rotated_pts[:, 1] = pts[:, 0] * sin_a + pts[:, 1] * cos_a
            
            # Translate to image center and scale
            pixel_pts = (rotated_pts * scale + np.array([width/2, height/2])).astype(np.int32)
            cv2.polylines(template, [pixel_pts], True, (0, 255, 0), 1)
            
        return template
