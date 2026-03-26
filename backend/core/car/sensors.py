import pygame
import math
from shapely.geometry import LineString, Point
from backend.core.config import SENSOR_LENGTH

class Sensors:
    def __init__(self, count, arc=90):
        self.count = count
        self.arc = arc

    def get_readings(self, car_pos, car_angle, track):
        readings = []
        # Distribute rays evenly in front of the car
        start_angle = car_angle - (self.arc / 2)
        step = self.arc / (self.count - 1) if self.count > 1 else 0

        car_point = Point(car_pos.x, car_pos.y)

        for i in range(self.count):
            angle = math.radians(start_angle + (i * step))
            
            # Create a ray from car to max length
            ray_end_x = car_pos.x + math.cos(angle) * SENSOR_LENGTH
            ray_end_y = car_pos.y - math.sin(angle) * SENSOR_LENGTH
            ray_line = LineString([(car_pos.x, car_pos.y), (ray_end_x, ray_end_y)])
            
            min_dist = SENSOR_LENGTH
            
            # Check intersection with all road boundaries (both outer and inner)
            for poly in track.road_polygons:
                # We care about the boundary (exterior and interiors)
                boundary = poly.boundary
                if ray_line.intersects(boundary):
                    intersection = ray_line.intersection(boundary)
                    if intersection.geom_type == 'Point':
                        dist = car_point.distance(intersection)
                        min_dist = min(min_dist, dist)
                    elif intersection.geom_type == 'MultiPoint':
                        for p in intersection.geoms:
                            dist = car_point.distance(p)
                            min_dist = min(min_dist, dist)
            
            # Check intersection with obstacles
            for poly in track.obstacle_polygons:
                boundary = poly.boundary
                if ray_line.intersects(boundary):
                    intersection = ray_line.intersection(boundary)
                    if intersection.geom_type == 'Point':
                        dist = car_point.distance(intersection)
                        min_dist = min(min_dist, dist)
                    elif intersection.geom_type == 'MultiPoint':
                        for p in intersection.geoms:
                            dist = car_point.distance(p)
                            min_dist = min(min_dist, dist)

            readings.append(min_dist)
        return readings

    def draw(self, screen, car_pos, car_angle, readings):
        """Visualize sensor rays for debugging."""
        start_angle = car_angle - (self.arc/2)
        step = self.arc/(self.count - 1) if self.count > 1 else 0

        for i, dist in enumerate(readings):
            angle = math.radians(start_angle + (i * step))
            end_x = car_pos.x + math.cos(angle) * dist
            end_y = car_pos.y - math.sin(angle) * dist
            pygame.draw.line(screen, (0, 255, 0), (car_pos.x, car_pos.y), (end_x, end_y), 1)
            pygame.draw.circle(screen, (255, 0, 0), (int(end_x), int(end_y)), 3)
