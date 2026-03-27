# Path Planning and Control

This document describes the vehicle control and trajectory planning algorithms implemented in the Autonomous Pilot AI simulation.

## PID Controller (`backend/controls/pid_controller.py`)

The Proportional-Integral-Derivative (PID) controller is responsible for maintaining the vehicle's lateral position (steering) and longitudinal speed (throttle).

*   **P (Proportional)**: Corrects the steering angle based on the immediate cross-track error (distance from the center of the lane).
*   **I (Integral)**: Accumulates past errors to eliminate steady-state bias (e.g., a constant wind or mechanical misalignment).
*   **D (Derivative)**: Predicts future error based on the rate of change, dampening the steering to prevent oscillations and overshooting.

*Usage*: The PID controller calculates a steering value between -1 and 1, which the bicycle kinematic model translates into wheel angles.

## Frenet Coordinates (`backend/planning/frenet.py`)

Instead of using standard Cartesian coordinates (X, Y) which make road-following mathematically complex, the simulation transforms the vehicle's position into the **Frenet-Serret** frame:
*   **s (Longitudinal)**: Distance traveled along the center of the lane.
*   **d (Lateral)**: Perpendicular distance from the center of the lane (offset).

*Advantage*: By converting (x, y) to (s, d), the Lane Follower simply tries to minimize `d` (keep it at 0) using the PID controller. A curved road becomes a straight line in the Frenet frame.

## Lane Follower (`backend/simulation/lane_follower.py`)

The Lane Follower combines Frenet conversion and PID control:
1. Calculates the closest point on the track centerline.
2. Determines the `d` offset (cross-track error).
3. Projects a "pre-aim" point ahead of the vehicle based on current speed to anticipate curves.
4. Feeds the error to the PID controller to output steering and throttle commands.
