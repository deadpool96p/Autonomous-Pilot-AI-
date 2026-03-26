import asyncio
import multiprocessing
import json
from backend.core.simulation.simulation import Simulation
from backend.core.genetic.population import Genome, create_population_from_saved
import time

class SimulationEngine(multiprocessing.Process):
    def __init__(self, simulation_id, track_data, track_file=None, initial_genome=None, queue=None):
        super().__init__()
        self.simulation_id = simulation_id
        self.track_data = track_data
        self.track_file = track_file
        self.initial_genome = initial_genome
        self.queue = queue
        self.stop_event = multiprocessing.Event()

    def run(self):
        try:
            print(f"[ENGINE] Starting simulation {self.simulation_id} process...")
            # Initialize headless simulation directly with track data dict
            sim = Simulation(headless=True, track_file=self.track_data)
            print(f"[ENGINE] Simulation {self.simulation_id} initialized with {len(sim.cars)} cars.")
        except Exception as e:
            import traceback
            print(f"[ENGINE ERROR] Failed to initialize simulation: {e}")
            traceback.print_exc()
            return

        print(f"[ENGINE] {self.simulation_id} entering main loop.")
        frame_count = 0

        while not self.stop_event.is_set():
            try:
                sim.update()
                
                # Prepare state update for frontend
                state = {
                    "type": "state",
                    "simulation_id": self.simulation_id,
                    "generation": sim.generation,
                    "cars": [
                        {
                            "pos": {"x": c.pos.x, "y": c.pos.y},
                            "angle": c.angle,
                            "alive": c.alive,
                            "sensors": c.sensors,
                            "last_checkpoint": c.last_checkpoint,
                            "progress": c.last_checkpoint / len(sim.track.checkpoints) if len(sim.track.checkpoints) > 0 else 0
                        } for c in sim.cars
                    ]
                }
                
                if self.queue:
                    # Non-blocking put to avoid stalls if receiver is slow
                    try:
                        self.queue.put_nowait(state)
                    except:
                        # If queue is full, skip this frame
                        pass
                
                # Control frequency
                time.sleep(0.05) # Slightly slower for stability
                frame_count += 1
                if frame_count % 100 == 0:
                    print(f"[ENGINE] {self.simulation_id} heartbeat: {frame_count} frames, {sum(1 for c in sim.cars if c.alive)} cars alive.")
            except Exception as e:
                import traceback
                print(f"[ENGINE ERROR] Simulation loop error: {e}")
                traceback.print_exc()
                time.sleep(1)

    def stop(self):
        self.stop_event.set()
