import cv2
import numpy as np

class LaneDetector:
    def __init__(self, img_width=1000, img_height=600):
        self.img_width = img_width
        self.img_height = img_height
        
        # Perspective Transform Points (Region of Interest)
        # Trapezoid mapping to a rectangle
        self.src_pts = np.float32([
            [img_width * 0.4, img_height * 0.6], 
            [img_width * 0.6, img_height * 0.6], 
            [img_width * 0.9, img_height * 0.9], 
            [img_width * 0.1, img_height * 0.9]
        ])
        
        self.dst_pts = np.float32([
            [img_width * 0.2, 0], 
            [img_width * 0.8, 0], 
            [img_width * 0.8, img_height], 
            [img_width * 0.2, img_height]
        ])
        
        self.M = cv2.getPerspectiveTransform(self.src_pts, self.dst_pts)
        self.M_inv = cv2.getPerspectiveTransform(self.dst_pts, self.src_pts)

    def process_frame(self, frame):
        """
        Processes a raw BGR frame and returns the detected lane visualization and offset.
        """
        # 1. Perspective Transform (Bird's Eye View)
        warped = cv2.warpPerspective(frame, self.M, (self.img_width, self.img_height), flags=cv2.INTER_LINEAR)
        
        # 2. Color filtering & Edge Detection
        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        
        # 3. Sliding window polynomial fit (Simplified Histogram Approach)
        histogram = np.sum(edges[self.img_height//2:, :], axis=0)
        midpoint = int(histogram.shape[0] / 2)
        
        leftx_base = np.argmax(histogram[:midpoint])
        rightx_base = np.argmax(histogram[midpoint:]) + midpoint
        
        # 4. Result dict
        offset = 0.0
        if leftx_base > 0 and rightx_base > midpoint:
            # Calculate lane center vs image center
            lane_center = (leftx_base + rightx_base) / 2.0
            image_center = self.img_width / 2.0
            offset = (lane_center - image_center) * 0.05 # pixels to approx meters
            
        visualization = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        cv2.circle(visualization, (int(leftx_base), self.img_height-50), 10, (0,255,0), -1)
        cv2.circle(visualization, (int(rightx_base), self.img_height-50), 10, (0,0,255), -1)
        
        return {
            "offset": offset,
            "warped": warped,
            "edges": visualization
        }
