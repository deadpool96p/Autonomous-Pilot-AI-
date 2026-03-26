import json
import numpy as np
from backend.database import SessionLocal
from backend import models

def seed_data():
    db = SessionLocal()
    if db.query(models.Track).count() == 0:
        # Default Rect Track
        with open("environment/tracks/default.json", "r") as f:
            t1_data = json.load(f)
        db.add(models.Track(name=t1_data["name"], json_data=t1_data))
        
        # Oval Track (Synthetic)
        oval_track = {
            "name": "Speed Oval",
            "spawn_point": {"x": 500, "y": 650, "angle": 0},
            "road_boundaries": [
                [[100, 400], [200, 200], [500, 100], [800, 200], [900, 400], [800, 600], [500, 700], [200, 600], [100, 400]],
                [[250, 400], [300, 300], [500, 250], [700, 300], [750, 400], [700, 500], [500, 550], [300, 500], [250, 400]]
            ],
            "obstacles": [],
            "checkpoints": []
        }
        # Add some checkpoints for the oval
        for i in range(0, 360, 30):
            rad = i * (3.14159 / 180)
            s_x, s_y = 500 + 400 * np.cos(rad), 400 + 300 * np.sin(rad)
            e_x, e_y = 500 + 250 * np.cos(rad), 400 + 150 * np.sin(rad)
            oval_track["checkpoints"].append({"start": [s_x, s_y], "end": [e_x, e_y]})
            
        db.add(models.Track(name=oval_track["name"], json_data=oval_track))
        db.commit()
    db.close()

if __name__ == "__main__":
    seed_data()
