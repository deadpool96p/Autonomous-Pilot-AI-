import os
import sys
import time
import json
import argparse
from queue import Queue

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.simulation.engine import SimulationEngine

def collect_data(duration_seconds=60):
    print(f"[*] Starting Automated Data Collection for {duration_seconds} seconds...")
    print(f"[*] Current Directory: {os.getcwd()}")
    
    # Ensure data directory exists
    os.makedirs("backend/data/tracks", exist_ok=True)
    track_path = "backend/data/tracks/test_track.json"
    
    if not os.path.exists(track_path):
        print(f"[!] Warning: {track_path} not found. Creating a simple oval track...")
        dummy_track = {
            "name": "Test Track",
            "roads": [{"points": [[100, 100], [900, 100], [900, 500], [100, 500], [100, 100]]}],
            "checkpoints": [{"points": [[500, 50], [500, 150]]}]
        }
        with open(track_path, "w") as f:
            json.dump(dummy_track, f)

    with open(track_path, "r") as f:
        track_data = json.load(f)

    state_queue = Queue()
    print(f"[*] Initializing Engine with track: {track_data.get('name')}")
    engine = SimulationEngine("collect_id", track_data, state_queue)
    
    # Configure for recording
    engine.mode = "ga" # Use GA to drive
    engine.recording = True
    
    print("[*] Starting Simulation Engine Thread...")
    engine.start()
    
    print("[*] Entering collection loop...")
    
    start_time = time.time()
    try:
        while time.time() - start_time < duration_seconds:
            if not engine.is_alive():
                print("\n[!] Engine thread died unexpectedly.")
                break
            
            # Print progress and check file count
            elapsed = time.time() - start_time
            img_count = 0
            if os.path.exists("backend/data/training/images"):
                img_count = len(os.listdir("backend/data/training/images"))
            
            sys.stdout.write(f"\r[*] Time: {elapsed:.1f}/{duration_seconds}s | Frames Collected: {img_count}")
            sys.stdout.flush()
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n[!] Collection interrupted by user.")
    finally:
        print("\n[*] Stopping Engine...")
        engine.stop()
        engine.join()
        
    final_count = 0
    if os.path.exists("backend/data/training/images"):
        final_count = len(os.listdir("backend/data/training/images"))
    print(f"[*] Data collection finished. Total frames: {final_count}")
    print(f"[*] Storage location: {os.path.abspath('backend/data/training/')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect behavioral cloning data from GA champion.")
    parser.add_argument("--duration", type=int, default=60, help="Duration of collection in seconds.")
    args = parser.parse_args()
    
    collect_data(args.duration)
