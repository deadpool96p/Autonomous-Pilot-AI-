import numpy as np
from backend.core.config import SENSOR_COUNT, HIDDEN_NODES

class NeuralNetwork:
    def __init__(self, input_nodes=SENSOR_COUNT, hidden_nodes=HIDDEN_NODES, output_nodes=2):
        self.input_nodes = input_nodes
        self.hidden_nodes = hidden_nodes
        self.output_nodes = output_nodes

    def predict(self, inputs, weights):
        # Split flat weights into matrices
        # W1: [input_nodes, hidden_nodes], W2: [hidden_nodes, output_nodes]
        # Biases: W1b: [hidden_nodes], W2b: [output_nodes]
        
        offset = 0
        w1_size = self.input_nodes * self.hidden_nodes
        w1 = weights[offset:offset+w1_size].reshape(self.input_nodes, self.hidden_nodes)
        offset += w1_size
        
        w1b = weights[offset:offset+self.hidden_nodes].reshape(1, self.hidden_nodes)
        offset += self.hidden_nodes
        
        w2_size = self.hidden_nodes * self.output_nodes
        w2 = weights[offset:offset+w2_size].reshape(self.hidden_nodes, self.output_nodes)
        offset += w2_size
        
        w2b = weights[offset:offset+self.output_nodes].reshape(1, self.output_nodes)
        
        # Forward pass with biases
        h = np.tanh(np.dot(inputs, w1) + w1b)
        out = np.tanh(np.dot(h, w2) + w2b)
        return out.flatten()