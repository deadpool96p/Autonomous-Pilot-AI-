def select(population):

    population.sort(key=lambda g: g.fitness, reverse=True)

    return population[:10]