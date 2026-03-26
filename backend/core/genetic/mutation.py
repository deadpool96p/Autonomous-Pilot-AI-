def mutate(weights):

    for i in range(len(weights)):

        if random.random() < 0.1:
            weights[i] += random.uniform(-1,1)