import cv2
import numpy as np
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

class ObjectDetector:
    def __init__(self, model_size='n'):
        # 'yolov8n.pt' is the nano model, fast for simulation
        self.enabled = HAS_YOLO
        if self.enabled:
            # Will download automatically if not present
            self.model = YOLO(f'yolov8{model_size}.pt') 
            print(f"[*] Loaded YOLOv8{model_size} model for object detection.")
        else:
            print("[!] ultralytics not installed. ObjectDetection disabled.")

    def detect(self, frame):
        """
        Runs YOLOv8 on the frame and returns bounding boxes for cars and pedestrians.
        COCO classes: 0 = person, 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
        """
        if not self.enabled:
            return []
            
        results = self.model(frame, verbose=False)
        detections = []
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Filter for relevant classes (Pedestrians and Vehicles)
                if cls_id in [0, 2, 3, 5, 7] and conf > 0.4:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    label = "pedestrian" if cls_id == 0 else "vehicle"
                    
                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "center_x": int((x1 + x2) / 2),
                        "center_y": int((y1 + y2) / 2)
                    })
                    
        return detections
