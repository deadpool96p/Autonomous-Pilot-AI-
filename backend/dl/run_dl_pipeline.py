import argparse
import os
import sys
import subprocess

def run_pipeline():
    parser = argparse.ArgumentParser(description="Unified DL Pipeline: Collect Data and Train Model.")
    parser.add_argument("--duration", type=int, default=60, help="Duration for data collection in seconds.")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size for training.")
    args = parser.parse_args()

    print("=== Step 1: Collecting Data ===")
    collect_cmd = [sys.executable, "-m", "backend.dl.collect_data", "--duration", str(args.duration)]
    try:
        subprocess.run(collect_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Data collection failed: {e}")
        return

    print("\n=== Step 2: Training Model ===")
    train_cmd = [sys.executable, "-m", "backend.dl.train", "--epochs", str(args.epochs), "--batch_size", str(args.batch_size)]
    try:
        subprocess.run(train_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Training failed: {e}")
        return

    print("\n=== Pipeline Complete ===")
    print("[*] You can now switch to DL mode in the UI and test the model.")

if __name__ == "__main__":
    run_pipeline()
