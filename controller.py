"""
Robot controller for executing planned actions
"""

import numpy as np


class RobotController:
    def __init__(self, simulator):
        """Initialize robot controller with simulation interface."""
        self.simulator = simulator
        self.max_joint_velocity = 2.0  # rad/s
        self.control_timestep = 0.01  # seconds

    def execute_plan(self, plan: list):
        """Execute action plan from planner."""
        for step in plan:
            action_type = step.get("action")
            if action_type == "move_to_ready":
                self.move_to_position(step["position"])
            elif action_type == "move_to_object":
                self.move_to_position(step["position"])
            elif action_type == "move_to_target":
                self.move_to_position(step["position"])
            elif action_type == "grasp":
                self.apply_grasp_force(step["force"])
            elif action_type == "release":
                self.apply_grasp_force(step["force"])

    def move_to_position(self, target_pos: np.ndarray, max_steps: int = 500):
        """
        Move end effector to target position using inverse kinematics.
        """
        target_pos = np.array(target_pos)
        print(f"Moving to position: {target_pos}")

        for step in range(max_steps):
            current_pos = self.simulator.get_body_pos("end_effector")
            if current_pos is None:
                print("Could not find end effector")
                break

            error = target_pos - current_pos
            error_norm = np.linalg.norm(error)

            if error_norm < 0.01:
                print(f"Reached target position at step {step}")
                break

            # Simple proportional control
            action = np.clip(error * 0.5, -1, 1)
            self.simulator.step(action, self.control_timestep)

    def apply_grasp_force(self, force: float):
        """Apply grasp force to gripper."""
        print(f"Applying grasp force: {force}")
        action = np.array([0, 0, 0, force])
        for _ in range(10):
            self.simulator.step(action, self.control_timestep)

    def get_robot_state(self) -> dict:
        """Get current robot state."""
        return self.simulator.get_state()
