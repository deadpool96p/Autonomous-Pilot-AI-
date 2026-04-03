import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, random_split
import os
import cv2
import pandas as pd
import numpy as np
import sys
import argparse
from tabulate import tabulate

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.simulation.neural import PilotNet

class DrivingDataset(Dataset):
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.csv_path = os.path.join(data_dir, "driving_log.csv")
        self.images_dir = os.path.join(data_dir, "images")
        
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Log file not found: {self.csv_path}")
            
        self.data = pd.read_csv(self.csv_path)
        print(f"[*] Loaded dataset with {len(self.data)} samples.")
        
    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        img_name = row["image_path"]
        img_path = os.path.join(self.images_dir, img_name)
        
        image = cv2.imread(img_path)
        if image is None:
            # Fallback for missing image
            print(f"[!] Warning: Image not found {img_path}")
            image = np.zeros((66, 200, 3), dtype=np.uint8)
            
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (200, 66))
        
        # Normalize to [0, 1] and CHW format
        image = image.astype(np.float32) / 255.0
        image = np.transpose(image, (2, 0, 1))
        
        label = np.array([row["steering"], row["throttle"]], dtype=np.float32)
        return torch.FloatTensor(image), torch.FloatTensor(label)

def train(epochs=10, batch_size=32):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Using device: {device}")
    
    model = PilotNet().to(device)
    
    data_dir = "backend/data/training"
    try:
        full_dataset = DrivingDataset(data_dir)
        if len(full_dataset) == 0:
            print("[!] Dataset is empty. Record some data first!")
            return
            
        # Split into train/validation (80/20)
        train_size = int(0.8 * len(full_dataset))
        val_size = len(full_dataset) - train_size
        train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
        
        print(f"[*] Training on {train_size} samples, validating on {val_size} samples.")
    except Exception as e:
        print(f"[!] Error loading dataset: {e}")
        return

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    criterion = nn.MSELoss()
    
    print(f"[*] Starting training for {epochs} epochs...")
    
    for epoch in range(epochs):
        # Training Phase
        model.train()
        train_loss = 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        # Validation Phase
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                
        print(f"Epoch {epoch+1}/{epochs} | Train Loss: {train_loss/len(train_loader):.6f} | Val Loss: {val_loss/len(val_loader):.6f}")

    # Save model
    os.makedirs("backend/models", exist_ok=True)
    save_path = "backend/models/steering_model.pth"
    torch.save(model.state_dict(), save_path)
    print(f"[*] Training complete. Model saved to {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PilotNet steering model.")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size.")
    args = parser.parse_args()
    
    train(epochs=args.epochs, batch_size=args.batch_size)
