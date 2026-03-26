import numpy as np
import random
import pickle
import os
from backend.core.config import POPULATION_SIZE, GENOME_SIZE, MUTATION_RATE

def load_best_genome(filename="saved_genome.pkl"):
    try:
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                return pickle.load(f)
    except Exception as e:
        print(f"Error loading genome: {e}")
    return None

def create_population_from_saved(saved_genome):
    new_pop = []
    # Elitism: keep the best one exactly
    new_pop.append(saved_genome)
    
    while len(new_pop) < POPULATION_SIZE:
        # Clone and mutate slightly
        mutated_weights = saved_genome.weights.copy()
        for i in range(len(mutated_weights)):
            if random.random() < 0.2: # High mutation for variation from champion
                mutated_weights[i] += np.random.normal(0, 0.05)
        new_pop.append(Genome(mutated_weights))
    return new_pop

class Genome:
    def __init__(self, weights=None):
        if weights is not None:
            self.weights = weights
        else:
            self.weights = np.random.uniform(-1, 1, GENOME_SIZE)
        self.fitness = 0

def evolve(population):
    # Sort by fitness
    population.sort(key=lambda x: x.fitness, reverse=True)
    best_genomes = population[:10]
    
    # Save the best of this generation for checkpointing
    try:
        os.makedirs("checkpoints", exist_ok=True)
        with open("checkpoints/best_car_latest.pkl", "wb") as f:
            pickle.dump(best_genomes[0], f)
    except: pass

    new_pop = []
    # Elitism: Keep the top 2
    new_pop.extend(best_genomes[:2])

    while len(new_pop) < POPULATION_SIZE:
        # Tournament Selection or simple top-10 random selection
        p1, p2 = random.sample(best_genomes, 2)
        
        # Uniform Crossover
        child_weights = np.zeros(GENOME_SIZE)
        for i in range(GENOME_SIZE):
            child_weights[i] = p1.weights[i] if random.random() < 0.5 else p2.weights[i]
        
        # Adaptive Mutation
        for i in range(GENOME_SIZE):
            if random.random() < MUTATION_RATE:
                child_weights[i] += np.random.normal(0, 0.1)
        
        new_pop.append(Genome(child_weights))
    return new_pop