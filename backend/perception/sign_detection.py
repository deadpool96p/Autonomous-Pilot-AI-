import cv2
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

class SignDetector:
    def __init__(self):
        self.enabled = HAS_YOLO
        if self.enabled:
            # We use standard YOLOv8n, but in a real-world scenario you'd fine-tune on a traffic sign dataset.
            # COCO class 11 = stop sign
            self.model = YOLO('yolov8n.pt') 
            print("[*] Loaded traffic sign detector.")

    def detect(self, frame):
        """
        Detect stop signs (Class 11 in COCO).
        For speed limits or yields, a specialized model is needed.
        """
        if not self.enabled:
            return []
            
        results = self.model(frame, verbose=False)
        signs = []
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                if cls_id == 11 and conf > 0.3:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    signs.append({
                        "type": "stop",
                        "confidence": conf,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)]
                    })
                    
        return signs
