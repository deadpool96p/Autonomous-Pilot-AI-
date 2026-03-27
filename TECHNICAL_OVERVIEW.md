# Technical Overview — Autonomous Pilot AI

## 1. Project Goal

Autonomous Pilot AI is a full-stack autonomous driving simulation platform. It provides a
browser-based environment where neural-network-controlled vehicles learn to navigate real-world
city road networks through evolutionary optimization (genetic algorithms) and supervised
learning (behavioral cloning via deep neural networks). The system imports actual street
topologies from OpenStreetMap, populates them with intelligent NPC traffic, and continuously
improves its driving models through an automated data collection and retraining pipeline.

## 2. System Architecture

```
┌───────────────────────────────────────────────────────┐
│                    React Frontend                     │
│  ┌────────────┐ ┌──────────────┐ ┌─────────────────┐  │
│  │ Canvas     │ │ Control      │ │ Stats / Collision│  │
│  │ Renderer   │ │ Panel        │ │ Dashboard        │  │
│  └─────┬──────┘ └──────┬───────┘ └────────┬─────────┘  │
│        │ WebSocket      │ HTTP REST        │            │
├────────┼────────────────┼──────────────────┼────────────┤
│        ▼                ▼                  ▼            │
│                   FastAPI Backend                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │               Simulation Engine                  │   │
│  │  ┌──────┐ ┌────────┐ ┌──────────┐ ┌───────────┐ │   │
│  │  │ Car  │ │ Sensors│ │ Genetic  │ │ Neural    │ │   │
│  │  │Physics│ │        │ │Algorithm │ │ Networks  │ │   │
│  │  └──────┘ └────────┘ └──────────┘ └───────────┘ │   │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────────────┐│   │
│  │  │ Track    │ │ Dynamic   │ │ Auto-Learning    ││   │
│  │  │ (HD Map) │ │ Objects   │ │ Manager          ││   │
│  │  └──────────┘ └───────────┘ └──────────────────┘│   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────┐  ┌─────────────────────────┐  │
│  │ Perception Pipeline  │  │ Planning & Control      │  │
│  │ - Lane Detection     │  │ - PID Controller        │  │
│  │ - Object Detection   │  │ - Frenet Planner        │  │
│  │ - Sign Detection     │  │ - Lane Follower         │  │
│  │ - Sensor Fusion      │  │                         │  │
│  └──────────────────────┘  └─────────────────────────┘  │
└───────────────────────────────────────────────────────┘
```

### Frontend (React + TypeScript + Vite)
- **SimulationCanvas**: HTML5 Canvas with a 60 FPS `requestAnimationFrame` loop. Renders roads, buildings, lane markings, traffic signs, dynamic objects, and car agents. Uses a `ResizeObserver` for responsive sizing.
- **ControlPanel**: Exposes track selection, intelligence mode switching, data recording, and training controls.
- **StatsPanel / CollisionStats**: Real-time telemetry fed by the WebSocket stream.
- **LaneVisualization**: Toggle controls for HD map overlay layers.

Communication uses a WebSocket connection (`/ws/{sim_id}`) for real-time state streaming (30–60 Hz) and REST endpoints (`/api/*`) for configuration changes.

### Backend (Python + FastAPI + Uvicorn)
- **main.py**: FastAPI application with REST endpoints for simulation lifecycle management and WebSocket broadcasting.
- **SimulationEngine**: Threaded game loop executing physics, sensor reads, neural inference, collision detection, fitness evaluation, and state serialization at ~60 Hz.

## 3. Core Modules

### 3.1 Car Physics (`backend/simulation/car.py`)
Implements a kinematic **bicycle model**:
- Steering angle maps to a front-wheel deflection limited to ±35°.
- Speed updates via a simplified acceleration model with linear drag.
- Position and heading are integrated using standard bicycle model equations:
  - `x += v * cos(θ) * dt`
  - `y += v * sin(θ) * dt`
  - `θ += (v / L) * tan(δ) * dt` where `L` is the wheelbase.

### 3.2 Sensors (`backend/simulation/sensors.py`)
- **Ray-cast distance sensors**: 8 rays spanning 160° from the car's heading. Each ray returns the distance to the nearest obstacle (track boundary, building, or dynamic object), capped at 150 units.
- **Camera view**: Generates a synthetic top-down image crop around the car for the DL pipeline.

### 3.3 Track Representation (`backend/simulation/track.py`)
Tracks are stored as JSON files containing:
- `roads[]`: Polylines with optional width, defining the drivable surface.
- `buildings[]`: Polygon outlines for visual context.
- `lanes[]`: HD lane geometries with left/right boundary polylines and marking types.
- `traffic_signs[]`: Position, type, and facing direction of regulatory signs.
- `graph`: Node-edge graph for NPC pathfinding.
- `checkpoints[]`: Ordered waypoints for fitness evaluation.
- `dynamic_objects[]`: Spawn descriptors for pedestrians and NPC vehicles.

### 3.4 Genetic Algorithm (`backend/simulation/genetic.py`)
- **Population**: 50 genomes, each a flat weight vector for a `SimpleFFN` neural network.
- **Selection**: Tournament selection of the top performers.
- **Crossover**: Uniform crossover between parent weight vectors.
- **Mutation**: Gaussian noise with adaptive mutation rate.
- **Fitness**: `checkpoints_reached * 100 + distance_traveled / 10 - collision_penalty`.

### 3.5 Neural Networks (`backend/simulation/neural.py`)
- **SimpleFFN**: Small feed-forward network (8 inputs → 16 → 2 outputs) used by GA agents.
- **PilotNet**: Convolutional neural network inspired by NVIDIA's architecture (3 conv layers → 3 FC layers) accepting 66×200 RGB images and outputting steering + throttle.

### 3.6 Data Collection & DL Training (`backend/dl/train.py`, `backend/auto_learning.py`)
- **Manual recording**: Captures camera views and action labels from the best-performing GA agent.
- **AutoLearningManager**: Background pipeline that automatically:
  1. Buffers up to 10,000 collision-free driving frames per track.
  2. Triggers asynchronous PilotNet retraining when the buffer is full.
  3. Versions models by track ID and timestamp (e.g., `steering_model_paris_20260327.pth`).

### 3.7 Dynamic Objects (`backend/simulation/objects.py`)
- **Pedestrian**: Graph-based waypoint navigation with forward/reverse patrol patterns.
- **NPCCar**: Implements the **Intelligent Driver Model (IDM)** for realistic car-following:
  - Acceleration is calculated as: `a = a_max * [1 - (v/v_des)^δ - (s*/s)^2]`
  - Where `s*` is the desired gap incorporating safe time headway and velocity differential.

### 3.8 Planning & Control (`backend/controls/`, `backend/planning/`)
- **PIDController**: Proportional-Integral-Derivative controller for steering correction based on cross-track error.
- **FrenetPath**: Converts Cartesian (x, y) positions to Frenet (s, d) coordinates relative to the road centerline.
- **LaneFollower**: Combines Frenet conversion with PID control and a speed-dependent look-ahead distance.

### 3.9 Perception Pipeline (`backend/perception/`)
- **LaneDetector**: OpenCV-based pipeline — perspective transform to bird's-eye view, Canny edge detection, histogram peak finding for left/right lane bases.
- **ObjectDetector**: YOLOv8 Nano inference wrapper filtering for COCO vehicle and pedestrian classes.
- **SignDetector**: YOLOv8-based stop sign detection (COCO class 11).
- **SensorFusion**: Pinhole camera model converting 2D bounding boxes to 3D world coordinates using known object widths and focal length geometry.

## 4. Workflow

### GA Evolution Cycle
```
Spawn 50 cars → Each uses SimpleFFN with individual genome weights
                  ↓
         Run physics/sensors/inference for each car at ~60 Hz
                  ↓
         Car collides → marked dead, fitness recorded
                  ↓
         All dead → Tournament selection + crossover + mutation
                  ↓
         New generation spawned → repeat
```

### DL Behavioral Cloning
```
GA produces skilled drivers → Record camera views + steering/throttle
                                      ↓
                      AutoLearningManager buffers 10k frames
                                      ↓
                      Background thread trains PilotNet (5 epochs)
                                      ↓
                      Model saved → Switch to DL mode → Load model
                                      ↓
                      PilotNet drives car from camera input
```

## 5. Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Axios |
| Backend | Python 3.8+, FastAPI, Uvicorn, WebSockets |
| ML/AI | PyTorch, NumPy, Ultralytics YOLOv8 |
| Computer Vision | OpenCV |
| Geospatial | OSMnx, Shapely, GeoPandas, NetworkX |
| Infrastructure | Concurrently (process manager), npm scripts |

## 6. Directory Structure

```
├── backend/
│   ├── main.py                  # FastAPI application & WebSocket server
│   ├── auto_learning.py         # Automated data pipeline manager
│   ├── controls/                # PID controller
│   ├── planning/                # Frenet coordinate conversion
│   ├── perception/              # Lane, object, sign detection + sensor fusion
│   ├── simulation/
│   │   ├── engine.py            # Core simulation loop
│   │   ├── car.py               # Vehicle physics (bicycle model)
│   │   ├── sensors.py           # Ray-cast and camera sensors
│   │   ├── track.py             # Track data loader
│   │   ├── genetic.py           # GA population & evolution
│   │   ├── neural.py            # SimpleFFN and PilotNet networks
│   │   ├── objects.py           # Pedestrian (waypoint) & NPCCar (IDM)
│   │   └── lane_follower.py     # Frenet + PID lane keeping
│   ├── dl/
│   │   └── train.py             # PilotNet training loop
│   ├── data/tracks/             # Track JSON files
│   ├── models/                  # Saved PyTorch model weights
│   └── utils/
│       └── import_osm.py        # OpenStreetMap → HD JSON converter
├── frontend/
│   └── src/
│       ├── App.tsx              # Main layout & state management
│       └── components/
│           ├── SimulationCanvas.tsx    # Canvas renderer
│           ├── ControlPanel.tsx        # Sidebar controls
│           ├── StatsPanel.tsx          # Metrics display
│           ├── CollisionStats.tsx      # Collision telemetry panel
│           └── LaneVisualization.tsx   # Perception overlay toggles
├── docs/
│   ├── pid_frenet.md            # PID & Frenet documentation
│   └── perception.md            # Perception pipeline documentation
├── USER_MANUAL.md               # End-user guide
├── TECHNICAL_OVERVIEW.md        # This document
└── README.md                    # Quick-start overview
```

## 7. Future Extensions

- **Traffic light state machines** with red/green cycle logic and vehicle response.
- **LIDAR simulation** generating synthetic point clouds for 3D perception models.
- **Reinforcement learning** (PPO/SAC) as an alternative to GA evolution.
- **Multi-agent cooperative driving** with V2V communication protocols.
- **Weather and lighting conditions** affecting sensor fidelity and physics.
- **Real-time model evaluation dashboards** with loss curves and validation metrics.
- **Scenario-based testing** (cut-in, emergency braking, intersection negotiation).
