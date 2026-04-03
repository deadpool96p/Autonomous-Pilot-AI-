"""
Procedural track generator for creating diverse training tracks.
Generates tracks with roads, checkpoints, lanes, and proper spawn points.
"""
import math
import random
import json
import os
import uuid
import numpy as np


def generate_oval_track(width=900, height=600, center_x=500, center_y=400, road_width=40):
    """Generates an oval/elliptical track."""
    num_points = 48
    outer_points = []
    inner_center = []
    checkpoints = []
    
    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points
        x = center_x + (width / 2) * math.cos(angle)
        y = center_y + (height / 2) * math.sin(angle)
        outer_points.append([round(x, 2), round(y, 2)])
        inner_center.append([round(x, 2), round(y, 2)])
    
    # Close the loop
    outer_points.append(outer_points[0])
    
    # Generate checkpoints every few points
    for i in range(0, num_points, 4):
        angle = (2 * math.pi * i) / num_points
        sx = center_x + (width / 2 + 30) * math.cos(angle)
        sy = center_y + (height / 2 + 30) * math.sin(angle)
        ex = center_x + (width / 2 - 30) * math.cos(angle)
        ey = center_y + (height / 2 - 30) * math.sin(angle)
        checkpoints.append({"points": [[round(sx, 2), round(sy, 2)], [round(ex, 2), round(ey, 2)]]})
    
    # Start position at the bottom of the oval
    start_x = center_x + (width / 2) * math.cos(math.pi / 2)
    start_y = center_y + (height / 2) * math.sin(math.pi / 2)
    
    return {
        "name": f"Speed Oval #{random.randint(100, 999)}",
        "roads": [{"points": outer_points, "width": road_width}],
        "checkpoints": checkpoints,
        "start_pos": [round(start_x, 2), round(start_y, 2)],
        "start_angle": 0,
        "lanes": [],
        "buildings": [],
        "traffic_signs": [],
        "dynamic_objects": []
    }


def generate_figure8_track(size=400, center_x=500, center_y=450, road_width=35):
    """Generates a figure-8 shaped track."""
    num_points = 36
    points = []
    checkpoints = []
    
    # Top loop
    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points
        x = center_x - size * 0.3 + (size * 0.3) * math.cos(angle)
        y = center_y - size * 0.3 + (size * 0.3) * math.sin(angle)
        points.append([round(x, 2), round(y, 2)])
    
    # Bottom loop (figure-8 crossover)
    for i in range(num_points):
        angle = -(2 * math.pi * i) / num_points  # Reverse direction for figure-8
        x = center_x + size * 0.3 + (size * 0.3) * math.cos(angle)
        y = center_y + size * 0.3 + (size * 0.3) * math.sin(angle)
        points.append([round(x, 2), round(y, 2)])
    
    points.append(points[0])  # Close loop
    
    # Checkpoints along the path
    for i in range(0, len(points) - 1, 6):
        p1 = points[i]
        checkpoints.append({"points": [p1, [p1[0] + 20, p1[1] + 20]]})
    
    return {
        "name": f"Figure-8 #{random.randint(100, 999)}",
        "roads": [{"points": points, "width": road_width}],
        "checkpoints": checkpoints,
        "start_pos": [round(points[0][0], 2), round(points[0][1], 2)],
        "start_angle": 0,
        "lanes": [],
        "buildings": [],
        "traffic_signs": [],
        "dynamic_objects": []
    }


def generate_city_grid_track(blocks_x=3, blocks_y=3, block_size=200, road_width=30, offset_x=100, offset_y=100):
    """Generates a city-grid style track with intersections."""
    roads = []
    checkpoints = []
    buildings = []
    traffic_signs = []
    
    grid_w = blocks_x * block_size
    grid_h = blocks_y * block_size
    
    # Horizontal roads
    for row in range(blocks_y + 1):
        y = offset_y + row * block_size
        road_pts = [[offset_x, y], [offset_x + grid_w, y]]
        roads.append({"points": road_pts, "width": road_width})
    
    # Vertical roads
    for col in range(blocks_x + 1):
        x = offset_x + col * block_size
        road_pts = [[x, offset_y], [x, offset_y + grid_h]]
        roads.append({"points": road_pts, "width": road_width})
    
    # Buildings in each city block
    margin = road_width / 2 + 10
    for row in range(blocks_y):
        for col in range(blocks_x):
            bx = offset_x + col * block_size + margin
            by = offset_y + row * block_size + margin
            bw = block_size - 2 * margin
            bh = block_size - 2 * margin
            if bw > 10 and bh > 10:
                buildings.append({
                    "points": [
                        [round(bx, 2), round(by, 2)],
                        [round(bx + bw, 2), round(by, 2)],
                        [round(bx + bw, 2), round(by + bh, 2)],
                        [round(bx, 2), round(by + bh, 2)]
                    ]
                })
    
    # Traffic signs at intersections
    for row in range(blocks_y + 1):
        for col in range(blocks_x + 1):
            x = offset_x + col * block_size
            y = offset_y + row * block_size
            sign_type = random.choice(["stop", "speed_limit_30", "speed_limit_50", "yield"])
            value = 30 if "30" in sign_type else 50 if "50" in sign_type else None
            traffic_signs.append({
                "position": [round(x + 12, 2), round(y + 12, 2)],
                "type": sign_type,
                "value": value
            })
    
    # Checkpoints along the first horizontal road
    for i in range(0, blocks_x + 1):
        cx = offset_x + i * block_size
        cy = offset_y
        checkpoints.append({"points": [[cx, cy - 15], [cx, cy + 15]]})
    
    start_x = offset_x + road_width
    start_y = offset_y
    
    return {
        "name": f"City Grid #{random.randint(100, 999)}",
        "roads": roads,
        "checkpoints": checkpoints,
        "start_pos": [round(start_x, 2), round(start_y, 2)],
        "start_angle": 0,
        "buildings": buildings,
        "traffic_signs": traffic_signs,
        "lanes": [],
        "dynamic_objects": []
    }


def generate_random_track():
    """Generates a random track from available types."""
    track_type = random.choice(["oval", "figure8", "city_grid"])
    
    if track_type == "oval":
        track = generate_oval_track(
            width=random.randint(300, 600),
            height=random.randint(200, 500),
            center_x=random.randint(350, 650),
            center_y=random.randint(300, 500),
            road_width=random.randint(30, 50)
        )
    elif track_type == "figure8":
        track = generate_figure8_track(
            size=random.randint(250, 450),
            center_x=random.randint(400, 600),
            center_y=random.randint(350, 550),
            road_width=random.randint(28, 45)
        )
    else:
        track = generate_city_grid_track(
            blocks_x=random.randint(2, 4),
            blocks_y=random.randint(2, 3),
            block_size=random.randint(150, 250),
            road_width=random.randint(25, 40)
        )
    
    return track


def save_track(track_data, tracks_dir="backend/data/tracks"):
    """Saves a generated track to the tracks directory."""
    os.makedirs(tracks_dir, exist_ok=True)
    
    track_id = f"generated_{uuid.uuid4().hex[:8]}"
    track_data["id"] = track_id
    
    filepath = os.path.join(tracks_dir, f"{track_id}.json")
    with open(filepath, "w") as f:
        json.dump(track_data, f, indent=2)
    
    return track_id, track_data
