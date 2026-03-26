SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
FPS = 60

# AI Config
POPULATION_SIZE = 50
SENSOR_COUNT = 5
SENSOR_LENGTH = 150
HIDDEN_NODES = 6

# Genetic Config
MUTATION_RATE = 0.1
# Weight count: (In * Hidden) + (Hidden) [bias] + (Hidden * Out) + (Out) [bias]
GENOME_SIZE = (SENSOR_COUNT * HIDDEN_NODES) + HIDDEN_NODES + (HIDDEN_NODES * 2) + 2

# Physics Config
SPAWN_X = 170
SPAWN_Y = 400
SPAWN_ANGLE = 0
WHEELBASE = 20
DRAG_COEFFICIENT = 0.05
MAX_SPEED = 10

# Track Config
ROAD_WIDTH = 60
TRACK_FILE = "environment/tracks/default.json"