class CarPhysics:

    def move(self, car):
        car.x += car.speed * car.direction_x
        car.y += car.speed * car.direction_y