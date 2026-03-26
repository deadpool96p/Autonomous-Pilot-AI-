def crossover(parent1, parent2):

    split = random.randint(0,len(parent1.weights))

    child = parent1.weights[:split] + parent2.weights[split:]

    return child