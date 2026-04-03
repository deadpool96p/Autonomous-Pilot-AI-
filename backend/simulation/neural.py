import torch
import torch.nn as nn
import numpy as np

class SimpleFFN(nn.Module):
    """FeedForward Neural Network for GA evolution."""
    def __init__(self, input_size=7, hidden_size=8, output_size=2):
        super(SimpleFFN, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.tanh(self.fc2(x)) # Steering and throttle usually -1 to 1
        return x
    
    def set_weights(self, weights):
        """Used by GA to set flat weights into model layers."""
        start = 0
        for param in self.parameters():
            numel = param.numel()
            param.data = torch.from_numpy(weights[start:start+numel]).view(param.shape).float()
            start += numel

    def get_weights(self):
        """Returns flat weights of the model."""
        return np.concatenate([p.data.numpy().flatten() for p in self.parameters()])

class PilotNet(nn.Module):
    """NVIDIA-style CNN for image-based behavioral cloning."""
    def __init__(self):
        super(PilotNet, self).__init__()
        self.conv_layers = nn.Sequential(
            nn.Conv2d(3, 24, 5, stride=2),
            nn.ELU(),
            nn.Conv2d(24, 36, 5, stride=2),
            nn.ELU(),
            nn.Conv2d(36, 48, 5, stride=2),
            nn.ELU(),
            nn.Conv2d(48, 64, 3),
            nn.ELU(),
            nn.Conv2d(64, 64, 3),
            nn.ELU(),
        )
        self.fc_layers = nn.Sequential(
            nn.Linear(64 * 1 * 18, 100),
            nn.ELU(),
            nn.Linear(100, 50),
            nn.ELU(),
            nn.Linear(50, 10),
            nn.ELU(),
            nn.Linear(10, 2), # [steering, throttle]
        )

    def forward(self, x):
        # x shape: (N, 3, 66, 200)
        x = self.conv_layers(x)
        x = x.view(x.size(0), -1)
        x = self.fc_layers(x)
        return x
