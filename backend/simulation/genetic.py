import numpy as np
import random

class Genome:
    def __init__(self, size):
        self.weights = np.random.randn(size)
        self.fitness = 0.0

    def mutate(self, rate=0.1, power=0.1):
        for i in range(len(self.weights)):
            if random.random() < rate:
                self.weights[i] += np.random.normal(0, power)

class Population:
    def __init__(self, size, genome_size):
        self.genomes = [Genome(genome_size) for _ in range(size)]
        self.generation = 1
        self.elite_count = 2

    def evolve(self):
        # Sort by fitness
        self.genomes.sort(key=lambda g: g.fitness, reverse=True)
        
        new_genomes = []
        
        # Elitism
        new_genomes.extend(self.genomes[:self.elite_count])
        
        # Mutation and crossover (simplified for now)
        while len(new_genomes) < len(self.genomes):
            # Select from top half
            parent = random.choice(self.genomes[:len(self.genomes)//2])
            child = Genome(len(parent.weights))
            child.weights = parent.weights.copy()
            child.mutate()
            new_genomes.append(child)
            
        self.genomes = new_genomes
        self.generation += 1
        print(f"[*] Evolving to generation {self.generation}")

    def reset_fitness(self):
        for g in self.genomes:
            g.fitness = 0.0
