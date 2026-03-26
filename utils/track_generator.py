import json

def generate_rect_track():
    # Outer: [100, 100] to [900, 700]
    # Inner: [250, 250] to [750, 550]
    # Road center approx: 175 left, 825 right, 175 top, 625 bottom
    
    track = {
        "name": "Advanced Rect Track",
        "spawn_point": {"x": 170, "y": 400, "angle": 90}, # Face UP
        "road_boundaries": [
            [[100, 100], [900, 100], [900, 700], [100, 700], [100, 100]],
            [[250, 250], [750, 250], [750, 550], [250, 550], [250, 250]]
        ],
        "obstacles": [],
        "checkpoints": []
    }
    
    # Generate checkpoints along the centerline
    # Left edge (down to up)
    for y in range(400, 175, -50):
        track["checkpoints"].append({"start": [100, y], "end": [250, y]})
    
    # Top edge (left to right)
    for x in range(175, 825, 50):
        track["checkpoints"].append({"start": [x, 100], "end": [x, 250]})
        
    # Right edge (top to bottom)
    for y in range(175, 625, 50):
        track["checkpoints"].append({"start": [750, y], "end": [900, y]})
        
    # Bottom edge (right to left)
    for x in range(825, 175, -50):
        track["checkpoints"].append({"start": [x, 550], "end": [x, 700]})
        
    # Left edge back to start (bottom to up)
    for y in range(625, 400, -50):
        track["checkpoints"].append({"start": [100, y], "end": [250, y]})
        
    with open("environment/tracks/default.json", "w") as f:
        json.dump(track, f, indent=4)

if __name__ == "__main__":
    generate_rect_track()
