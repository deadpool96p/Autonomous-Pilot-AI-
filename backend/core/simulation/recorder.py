import os
import pandas as pd
from datetime import datetime

class DataRecorder:
    def __init__(self, data_dir="backend/data"):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.current_file = None
        self.buffer = []

    def start_session(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_file = os.path.join(self.data_dir, f"driving_log_{timestamp}.csv")
        self.buffer = []
        print(f"[RECORDER] Started new session: {self.current_file}")

    def record(self, sensors, speed, steering, throttle):
        if self.current_file:
            row = {f"sensor_{i}": s for i, s in enumerate(sensors)}
            row.update({
                "speed": speed,
                "steering": steering,
                "throttle": throttle
            })
            self.buffer.append(row)
            
            # Save every 100 frames to avoid memory bloat
            if len(self.buffer) >= 100:
                self.flush()

    def flush(self):
        if self.current_file and self.buffer:
            df = pd.DataFrame(self.buffer)
            # Append if file exists, else write headers
            mode = 'a' if os.path.exists(self.current_file) else 'w'
            header = not os.path.exists(self.current_file)
            df.to_csv(self.current_file, mode=mode, header=header, index=False)
            self.buffer = []

    def stop_session(self):
        if self.current_file:
            self.flush()
            print(f"[RECORDER] Session stopped. Total frames recorded.")
            self.current_file = None
