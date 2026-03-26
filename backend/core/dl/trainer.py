import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import os
from backend.core.dl.model import DrivingModel

class DrivingDataset(Dataset):
    def __init__(self, csv_file):
        self.data = pd.read_csv(csv_file)
        self.sensors = self.data[[c for c in self.data.columns if "sensor_" in c]].values.astype(np.float32)
        # Normalize sensors (0-150 -> 0-1)
        self.sensors = self.sensors / 150.0
        self.labels = self.data[["steering", "throttle"]].values.astype(np.float32)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.sensors[idx], self.labels[idx]

def train_bc(csv_file, epochs=50, batch_size=32, model_path="backend/data/best_model.pth"):
    if not os.path.exists(csv_file):
        print(f"[TRAINER] Error: File {csv_file} not found.")
        return None

    dataset = DrivingDataset(csv_file)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    input_size = dataset.sensors.shape[1]
    model = DrivingModel(input_size=input_size)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    print(f"[TRAINER] Starting training on {len(dataset)} samples...")
    for epoch in range(epochs):
        epoch_loss = 0
        for sensors, labels in dataloader:
            optimizer.zero_grad()
            outputs = model(sensors)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        if (epoch + 1) % 10 == 0:
            print(f"[TRAINER] Epoch {epoch+1}/{epochs}, Loss: {epoch_loss/len(dataloader):.4f}")

    torch.save(model.state_dict(), model_path)
    print(f"[TRAINER] Model saved to {model_path}")
    return model_path
