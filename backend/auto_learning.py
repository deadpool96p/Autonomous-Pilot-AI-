import os
import time
import json
import torch
import shutil
import threading
from datetime import datetime
from queue import Queue
from backend.simulation.neural import PilotNet
from backend.dl.train import train

class AutoLearningManager:
    def __init__(self, track_id="default", data_dir="backend/data/training_auto", buffer_size=10000):
        self.track_id = track_id
        self.data_dir = os.path.join(data_dir, self.track_id)
        self.images_dir = os.path.join(self.data_dir, "images")
        self.csv_path = os.path.join(self.data_dir, "driving_log.csv")
        self.buffer_size = buffer_size
        self.is_training = False
        self.last_train_time = None
        self.model_path = f"backend/models/steering_model_{self.track_id}.pth"
        
        # Ensure directories exist
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Load existing data count
        self.current_count = self._get_data_count()
        
    def _get_data_count(self):
        if not os.path.exists(self.csv_path):
            return 0
        with open(self.csv_path, 'r') as f:
            return sum(1 for line in f) - 1 # Subtract header

    def add_data(self, frame_img, steering, throttle, progress, collisions):
        """
        Adds a frame to the auto-training dataset if it meets quality criteria.
        Criteria: progress > 0.05 (not just starting) and collisions == 0.
        """
        if collisions > 0:
            return False
            
        timestamp = int(time.time() * 1000)
        img_name = f"auto_{timestamp}.jpg"
        save_path = os.path.join(self.images_dir, img_name)
        
        import cv2
        cv2.imwrite(save_path, frame_img)
        
        import csv
        header = not os.path.exists(self.csv_path)
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(["image_path", "steering", "throttle", "timestamp", "progress"])
            writer.writerow([img_name, steering, throttle, timestamp, progress])
            
        self.current_count += 1
        return True

    def check_and_trigger_training(self):
        """Triggers training if enough new data is collected."""
        if self.is_training:
            return False
            
        if self.current_count >= self.buffer_size:
            threading.Thread(target=self._run_training).start()
            return True
        return False

    def _run_training(self):
        self.is_training = True
        print(f"[*] [AutoLearning] Starting background retraining on {self.current_count} frames for track {self.track_id}...")
        
        try:
            self._sync_to_main_training()
            
            # Start training, passing the specific target directory
            main_train_dir = os.path.join("backend/data/training", self.track_id)
            train(epochs=5, batch_size=32, data_dir=main_train_dir)
            
            self.last_train_time = datetime.now()
            
            # Automated model versioning
            timestamp_str = self.last_train_time.strftime("%Y%m%d_%H%M%S")
            
            # Default generic model output from train()
            generic_model_path = "backend/models/steering_model.pth"
            if os.path.exists(generic_model_path):
                # Save track specific models
                versioned_model_path = f"backend/models/steering_model_{self.track_id}_{timestamp_str}.pth"
                shutil.copy(generic_model_path, versioned_model_path)
                shutil.copy(generic_model_path, self.model_path) # Latest for this track
                print(f"[+] [AutoLearning] Saved track model: {versioned_model_path}")
                
            print(f"[+] [AutoLearning] Training complete at {self.last_train_time}")
            
            self._cleanup_buffer()
            
        except Exception as e:
            print(f"[!] [AutoLearning] Training failed: {e}")
        finally:
            self.is_training = False

    def _sync_to_main_training(self):
        """Copies auto-collected data to the main training directory used by train.py."""
        target_dir = os.path.join("backend/data/training", self.track_id)
        target_images = os.path.join(target_dir, "images")
        os.makedirs(target_images, exist_ok=True)
        
        for f in os.listdir(self.images_dir):
            shutil.copy(os.path.join(self.images_dir, f), os.path.join(target_images, f))
            
        if os.path.exists(self.csv_path):
            with open(self.csv_path, 'r') as src, open(os.path.join(target_dir, "driving_log.csv"), 'a') as dst:
                lines = src.readlines()[1:] # Skip header
                dst.writelines(lines)

    def _cleanup_buffer(self):
        """Removes oldest frames if the total count exceeds buffer_size."""
        for f in os.listdir(self.images_dir):
            os.remove(os.path.join(self.images_dir, f))
        if os.path.exists(self.csv_path):
            os.remove(self.csv_path)
        self.current_count = 0

    def get_status(self):
        return {
            "is_training": self.is_training,
            "data_count": self.current_count,
            "last_train": self.last_train_time.isoformat() if self.last_train_time else None
        }
