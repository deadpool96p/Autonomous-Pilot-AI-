import random
import json
import os

def generate_random_track(width=1000, height=800):
    name = f"Random Track {random.randint(100, 999)}"
    spawn_point = {"x": 100, "y": 100, "angle": 0}
    
    # Simple procedural track: several points in a loop
    num_points = 8
    center_x, center_y = width // 2, height // 2
    outer_radius = min(width, height) // 2 - 50
    inner_radius = outer_radius - 120
    
    outer_boundary = []
    inner_boundary = []
    
    for i in range(num_points + 1):
        angle = (i / num_points) * 2 * 3.14159
        # Add some noise
        noise_outer = random.uniform(-20, 20)
        noise_inner = random.uniform(-20, 20)
        
        r_out = outer_radius + noise_outer
        r_in = inner_radius + noise_inner
        
        outer_boundary.append([center_x + r_out * 1.2 * random.uniform(0.8, 1.2) * (1 if i%2==0 else 0.9), 
                               center_y + r_out * 0.8 * random.uniform(0.8, 1.2)]) # To make it elliptical
        # Actually let's just do a simple circle-ish loop for now
        
    # Reset to a better loop
    outer_boundary = []
    inner_boundary = []
    for i in range(num_points):
        angle = (i / num_points) * 2 * 3.14159
        r = outer_radius * (1 + 0.2 * random.uniform(-1, 1))
        outer_boundary.append([center_x + r * 1.5 * (0.8 * (i/num_points) + 0.5) * (1.2 if i%3==0 else 1.0), 
                               center_y + r * (1.0 if i%2==0 else 0.8)])
    
    # Use a more reliable way: jittered circle
    outer_boundary = []
    inner_boundary = []
    for i in range(num_points):
        a = (i / num_points) * 2 * 3.14159
        r_off = random.uniform(0.8, 1.2)
        ox = center_x + math.cos(a) * outer_radius * r_off
        oy = center_y + math.sin(a) * outer_radius * r_off
        outer_boundary.append([ox, oy])
        
        ix = center_x + math.cos(a) * inner_radius * r_off
        iy = center_y + math.sin(a) * inner_radius * r_off
        inner_boundary.append([ix, iy])
        
    outer_boundary.append(outer_boundary[0])
    inner_boundary.append(inner_boundary[0])
    
    checkpoints = []
    for i in range(num_points):
        checkpoints.append({
            "start": outer_boundary[i],
            "end": inner_boundary[i]
        })
        
    track_data = {
        "name": name,
        "spawn_point": {"x": (outer_boundary[0][0] + inner_boundary[0][0])/2, 
                        "y": (outer_boundary[0][1] + inner_boundary[0][1])/2, 
                        "angle": 90},
        "road_boundaries": [outer_boundary, inner_boundary],
        "obstacles": [],
        "checkpoints": checkpoints
    }
    return track_data

import math # Needed for cos/sin
