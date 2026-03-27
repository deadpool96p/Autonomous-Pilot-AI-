# Perception Pipeline

The simulation features a complete, multi-stage perception pipeline for the ego vehicle, transitioning raw pixel data into actionable 3D world coordinates.

## 1. Lane Detection (`backend/perception/lane_detection.py`)
Utilizes classical Computer Vision (OpenCV) to identify drivable boundaries:
*   **Perspective Transform**: Warps the front-facing camera view into a Top-Down "Bird's Eye" view.
*   **Edge Detection**: Applies Gaussian Blur followed by Canny Edge Detection to isolate lane markings.
*   **Histogram Peak & Sliding Window**: Processes the binary edge image by taking a column-wise sum (histogram) to find the base of the left and right lane lines, calculating the lane center offset.

## 2. Object Detection (`backend/perception/object_detection.py`)
Utilizes a Deep Neural Network (YOLOv8 Nano) for real-time inference:
*   Identifies dynamic objects (Cars, Trucks, Buses, Pedestrians) from the COCO dataset.
*   Outputs 2D bounding boxes `[x1, y1, x2, y2]` and confidence scores.

## 3. Traffic Sign Recognition (`backend/perception/sign_detection.py`)
*   Scans the environment for critical regulatory signs (e.g., Stop Signs, Yield, Speed Limits).
*   Implemented via YOLOv8, isolating specific classes to trigger control overrides (e.g., forcing the PID controller to brake at a stop sign).

## 4. Sensor Fusion (`backend/perception/sensor_fusion.py`)
Bridging 2D pixels to 3D simulation space:
*   Takes the 2D bounding boxes from YOLOv8.
*   Uses a **Pinhole Camera Model** and width heuristics (e.g., a car is ~1.8m wide) to estimate depth.
*   Projects the relative depth and azimuthal angle onto the map's global (X, Y) coordinate system, allowing the path planner to react to obstacles.
