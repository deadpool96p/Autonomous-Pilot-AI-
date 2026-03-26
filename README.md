# 🏎️ AI Autonomous Pilot Simulation

A professional, full-stack autonomous vehicle simulation where cars learn to navigate complex tracks using **Genetic Algorithms (GA)** and **Neural Networks (NN)**. 

Built with a high-performance **FastAPI** backend and a modern **React + TypeScript** frontend with real-time **WebSocket** telemetry.

![Simulation Dashboard](https://via.placeholder.com/1000x600?text=Autonomous+Pilot+Simulation+Live+View)

## 🌟 Key Features

- **Brain-Powered Driving**: Each car is controlled by a feedforward neural network that processes 5-9 sensor rays to navigate track boundaries.
- **Genetic Evolution**: Generations of cars evolve through selection, crossover, and mutation, specifically rewarded for progressive checkpoint completion.
- **Robust Full-Stack Architecture**: 
  - **Backend**: FastAPI manages the simulation engine, track generation, and AI state.
  - **Frontend**: React (Vite) + Tailwind CSS provides a premium dashboard with real-time HUD and visual telemetry.
- **Bicycle Model Physics**: Implements realistic kinematics for smooth, drift-aware movement.
- **Dynamic Track Gallery**: Includes several pre-defined tracks (Oval, Winding, Obstacles) and a **Procedural Track Generator**.
- **Persistence**: Save and Load trained "Champion" genomes to resume evolution sessions.

## 🛠️ Technology Stack

- **Core Logic**: Python 3.8+, NumPy, Shapely (Geometry).
- **Backend**: FastAPI, Uvicorn, WebSockets.
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide-React.
- **Graphics**: HTML5 Canvas API (Frontend), Pygame (Backend Geometry Masking).

## 🚀 Getting Started

### Prerequisites
- **Python 3.8+** (Must be in your PATH)
- **Node.js 16+** & **npm**

### Quick Start (One Command)
We've unified the entire startup process. Simply run the following in the project root:

```powershell
npm start
```
*This command will automatically install Python and NPM dependencies and launch both servers.*

- **Dashboard**: `http://localhost:5173`
- **API (Backend)**: `http://localhost:8000`

## 🎮 How to Use

1. **Select a Track**: Use the sidebar to pick between different courses or generate a new one.
2. **Initialize Simulation**: Click **"Initialize System"** to spawn the first generation (50 agents).
3. **Monitor Progress**: Watch the real-time HUD for "Active Agents", "Generation", and "Best Progress".
4. **Iterative Learning**: As cars collide, the system automatically evolves the next generation based on fitness.
5. **Save/Load**: Use the Persistence buttons to save the current best genome for later use.

## 📂 Project Structure

```text
├── backend/
│   ├── core/               # Simulation Engine, AI, and Environment logic
│   │   ├── ai/             # Neural Network definitions
│   │   ├── environment/    # Tracks and procedural generators
│   │   └── simulation/     # Master simulation controller and fitness logic
│   ├── main.py             # FastAPI entry point
│   └── simulation_runner.py # Multiprocessing process manager
├── frontend/
│   ├── src/
│   │   ├── components/     # UI and Canvas rendering
│   │   └── App.tsx         # Main Dashboard logic
│   └── vite.config.ts      # Proxy and dev server config
└── package.json            # Unified dependencies and scripts
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.
