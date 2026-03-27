# User Manual — Autonomous Pilot AI

## 1. Prerequisites

| Requirement | Minimum Version |
|---|---|
| Python | 3.8+ |
| Node.js | 16+ |
| npm | 8+ |
| Git | Any recent |

Hardware: Any modern CPU is sufficient. A CUDA-compatible GPU accelerates Deep Learning training but is not required.

## 2. Installation & Startup

```bash
# 1. Clone the repository
git clone https://github.com/deadpool96p/Autonomous-Pilot-AI-.git
cd Autonomous-Pilot-AI-

# 2. Install Python dependencies (automatic on first start)
pip install -r backend/requirements.txt

# 3. Install Node dependencies
cd frontend && npm install && cd ..

# 4. Start the full application
npm start
```

This starts both the FastAPI backend on `http://localhost:8000` and the React frontend on `http://localhost:5173`. Open `http://localhost:5173` in a browser.

## 3. Frontend Controls Reference

### Top Header Bar

| Control | Description |
|---|---|
| **Reset Simulation** | Clears all training data and reloads the application. Use with caution. |
| **Import Track** | (Future) Opens a dialog to upload a custom track JSON file. |
| **Connected / Disconnected** | Status indicator. Green = WebSocket link active, Red = no active simulation. |

### Left Sidebar

#### Track Selection
- **Active Track dropdown** – Choose from available city maps and the default test track.
- **Pick Random Track** – Randomly selects one of the loaded tracks.
- **Generate New Track** – Opens import settings to generate a track from OpenStreetMap data.
- **Show Dynamic Objects** – Toggles visibility of NPC cars and pedestrians on the canvas.

#### Intelligence Mode
- **Evolution (GA)** – Uses a genetic algorithm to evolve 50 neural network agents simultaneously. Best suited for initial exploration and training data generation.
- **Deep Learning (DL)** – Runs a single car with a pre-trained PilotNet CNN. Requires a trained model file.
- **Lane Follow (PID)** – Runs a single car using the PID lane-keeping controller. Works best on road networks with clear centerlines.

#### Data & Training
- **Record Data** (toggle) – Enables manual frame capture from the best GA car to build a behavioral cloning dataset.
- **Train Model** – Launches a PilotNet training session using the collected driving data.
- **Load Model** – Reloads the latest `steering_model.pth` into the DL pipeline.

#### Perception Overlays
- **HD Lane Boundaries & Signs** – Toggles rendering of lane edge lines and traffic sign markers.
- **PID Lookahead / Trajectory** – Toggles rendering of PID tracking path overlays.

### Bottom Overlay
- **Start / Stop** – Begins or halts the simulation loop.

### Real-Time Metrics Panel

| Metric | Meaning |
|---|---|
| **Generation Cycle** | Current GA generation number. Increments each time all 50 agents die. |
| **Active Agents** | Number of cars still alive in the current generation. |
| **Peak Fitness** | Highest fitness score achieved by any car this generation. |
| **Auto-Learning Pipeline** | Shows "COLLECTING" while buffering frames, "TRAINING" during background retraining. |
| **Collision Telemetry** | Pedestrian hits, NPC collisions, boundary faults, and clean completions. |

## 4. How Each Mode Works

### Genetic Algorithm (GA)
1. 50 cars spawn simultaneously, each controlled by a small feed-forward neural network with random weights.
2. Cars navigate using 8 directional distance sensors.
3. When all cars crash, fitness scores are calculated (distance + checkpoints).
4. The top performers reproduce via crossover and mutation to create the next generation.
5. Over many generations, cars learn to navigate the track.

### Deep Learning (DL)
1. First, collect data by running GA mode with recording enabled (or rely on the auto-learning pipeline).
2. The system captures camera views and steering/throttle labels.
3. Train a PilotNet CNN on this dataset via "Train Model".
4. Switch to DL mode and click "Load Model" to drive using the trained network.

### PID Lane Following
1. The PID controller reads the lane centerline from the HD map data.
2. It calculates the cross-track error (distance from center) and converts it into steering corrections.
3. Works autonomously without any training data—ideal for testing track geometry.

## 5. Troubleshooting

| Problem | Solution |
|---|---|
| **Cars not moving** | Ensure you clicked "Start" (bottom overlay button) after initialization. Check the terminal for Python errors. |
| **WebSocket Disconnected** | The backend may have crashed. Check the terminal for stack traces. Restart with `npm start`. |
| **0 Active Agents** | All cars may have immediately collided. Try a wider track or the test track first. |
| **DL model not driving** | Ensure `backend/models/steering_model.pth` exists. Train a model first or use GA mode. |
| **Track not rendering** | Verify that `.json` track files exist in `backend/data/tracks/`. Re-generate with the OSM importer if needed. |
| **Port in use** | Kill any processes on ports 8000 / 5173, then restart. |
| **Proxy errors on startup** | These appear briefly while the backend boots. They resolve once Uvicorn is ready (usually 2–3 seconds). |
