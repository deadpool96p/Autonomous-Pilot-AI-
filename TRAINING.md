# Training Guide: Genetic Algorithm & Deep Learning

This simulation supports two modes of autonomous driving: **Evolution (GA)** and **Vision-based Deep Learning (DL)**.

## 1. Genetic Algorithm (GA)
In GA mode, cars evolve a simple neural network by navigating the track.
- **How to start**: Open the UI, select a track, ensure "Evolution (GA)" is selected, and press **Start Simulation**.
- **Optimization**: Let this run for a few generations until cars can navigate most of the track.

## 2. Deep Learning (Behavioral Cloning)
In DL mode, a single car is controlled by a PilotNet CNN that processes simulated camera images.

### Step 2.1: Unified Pipeline (Recommended)
You can run the entire data collection and training process in one command:
```bash
python -m backend.dl.run_dl_pipeline --duration 60 --epochs 10
```
This will:
1. Run the simulation for 60 seconds to collect frames from the best GA cars.
2. Automatically start training the PilotNet model on the collected data.
3. Save the model to `backend/models/steering_model.pth`.

### Step 2.2: Manual Steps
Alternatively, you can run the steps manually:
- **Collect Data**: 
  ```bash
  python -m backend.dl.collect_data --duration 60
  ```
- **Train Model**:
  ```bash
  python -m backend.dl.train --epochs 10
  ```

### Step 2.3: Inference
1. In the UI, select **Deep Learning (DL)** mode.
2. Click **Reload / Load Model** to ensure the latest weights are active.
3. Press **Start Simulation**.
4. The car (blue) will now use the trained model to drive based on visual input.

---

## Troubleshooting
- **NameError: argparse**: Fixed. Ensure you are using the latest `backend/dl/train.py`.
- **Validation Split**: The trainer now automatically splits data 80/20 for training and validation.
- **CUDA/GPU**: Training automatically uses CUDA if available for faster processing.
