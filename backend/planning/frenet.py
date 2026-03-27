import math
import numpy as np
from shapely.geometry import LineString, Point

class FrenetPath:
    def __init__(self, target_course):
        """
        target_course: list of [x, y] representing the centerline
        """
        self.course = target_course
        self.line = LineString(self.course)
        
    def get_frenet(self, x, y):
        """
        Convert (x, y) to (s, d)
        s: arc length along the centerline
        d: lateral offset from the centerline
        """
        p = Point(x, y)
        s = self.line.project(p) # distance along the line
        
        # To get d (signed distance), we need to know left or right.
        # Find the perpendicular distance to the line.
        closest_point = self.line.interpolate(s)
        d_mag = p.distance(closest_point)
        
        # Find the segment to determine direction (left > 0, right < 0)
        coords = list(self.line.coords)
        segment_idx = 0
        current_s = 0.0
        
        for i in range(len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i+1]
            seg_len = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
            if current_s + seg_len >= s:
                segment_idx = i
                break
            current_s += seg_len
            
        p1 = coords[segment_idx]
        p2 = coords[min(segment_idx+1, len(coords)-1)]
        
        # Cross product to determine side
        # vector math: (p2.x - p1.x)*(py - p1.y) - (p2.y - p1.y)*(px - p1.x)
        cross = (p2[0] - p1[0]) * (y - p1[1]) - (p2[1] - p1[1]) * (x - p1[0])
        sign = 1.0 if cross > 0 else -1.0
        
        return s, d_mag * sign

    def get_cartesian(self, s, d):
        """
        Convert (s, d) back to (x, y)
        """
        s = max(0, min(s, self.line.length))
        base_pt = self.line.interpolate(s)
        
        # We need the tangent at s
        delta_s = 0.5
        s1 = max(0, s - delta_s)
        s2 = min(self.line.length, s + delta_s)
        pt1 = self.line.interpolate(s1)
        pt2 = self.line.interpolate(s2)
        
        theta = math.atan2(pt2.y - pt1.y, pt2.x - pt1.x)
        
        # normal vector is angle + 90 deg (math.pi / 2)
        normal_angle = theta + math.pi / 2
        
        x = base_pt.x + d * math.cos(normal_angle)
        y = base_pt.y + d * math.sin(normal_angle)
        
        return x, y, theta
