def calculate_fitness(car):
    # Base fitness on checkpoints passed
    checkpoint_reward = (car.last_checkpoint + 1) * 100
    
    # distance and speed are secondary bonuses to encourage faster completion
    speed_bonus = (car.distance / car.time_alive * 2) if car.time_alive > 0 else 0
    
    time_penalty = car.time_alive * 0.01
    collision_penalty = 50 if car.collided else 0
    
    return checkpoint_reward + speed_bonus - time_penalty - collision_penalty