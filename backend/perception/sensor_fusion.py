import math

class SensorFusion:
    def __init__(self, camera_fov=90.0, image_width=1000):
        self.fov = math.radians(camera_fov)
        self.image_width = image_width
        self.focal_length = (image_width / 2) / math.tan(self.fov / 2)
        
        # Ground truth widths (approximate, in meters)
        self.real_widths = {
            "pedestrian": 0.6,
            "vehicle": 1.8,
            "stop": 0.8
        }

    def process_detections(self, detections, car_x, car_y, car_yaw):
        """
        Projects 2D image bounding boxes into 3D world space using distance heuristics.
        Distance = (Real_Width * Focal_Length) / Pixel_Width
        """
        tracked_objects = []
        
        for det in detections:
            label = det.get("label", det.get("type"))
            if label not in self.real_widths:
                continue
                
            x1, y1, x2, y2 = det["bbox"]
            pixel_width = max(1, x2 - x1)
            
            # Simple inverse perspective mapping for depth
            distance = (self.real_widths[label] * self.focal_length) / pixel_width
            
            # Angle relative to camera center
            center_x = (x1 + x2) / 2
            dx_pixels = center_x - (self.image_width / 2)
            angle_offset = math.atan2(dx_pixels, self.focal_length)
            
            # Global coordinates
            global_angle = car_yaw + angle_offset
            obj_x = car_x + distance * math.cos(global_angle)
            obj_y = car_y + distance * math.sin(global_angle)
            
            tracked_objects.append({
                "label": label,
                "distance": distance,
                "world_x": obj_x,
                "world_y": obj_y,
                "confidence": det["confidence"]
            })
            
        return tracked_objects
