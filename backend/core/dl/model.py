import torch
import torch.nn as nn

class DrivingModel(nn.Module):
    def __init__(self, input_size=5, hidden_size=64, output_size=2):
        super(DrivingModel, self).__init__()
        self.input_layer = nn.Linear(input_size, hidden_size)
        self.hidden_layer = nn.Linear(hidden_size, hidden_size)
        self.output_layer = nn.Linear(hidden_size, output_size)
        self.relu = nn.ReLU()
        self.tanh = nn.Tanh()

    def forward(self, x):
        x = self.relu(self.input_layer(x))
        x = self.relu(self.hidden_layer(x))
        x = self.tanh(self.output_layer(x))
        return x
