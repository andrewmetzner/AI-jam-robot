"""Rover core controller."""

from typing import Dict, Tuple
import numpy as np


class Rover:
    def __init__(self, position: Tuple[float, float] = (0, 0)):
        """Initialize rover."""
        self.position = np.array(position, dtype=np.float32)
        self.orientation = 0.0  # radians
        self.velocity = np.array([0.0, 0.0], dtype=np.float32)
        self.battery = 100.0  # percentage
        self.samples_collected = []
        self.state_history = []

    def move_to(self, target: Tuple[float, float], step_size: float = 0.1):
        """Move rover towards target position."""
        target = np.array(target, dtype=np.float32)
        direction = target - self.position
        distance = np.linalg.norm(direction)

        if distance > 0.01:
            direction = direction / distance
            self.position = self.position + direction * step_size
            self.velocity = direction * step_size
            self.battery -= 0.1  # consume battery
            self._record_state()

    def collect_sample(self, sample_id: int, rock_type: str = "unknown"):
        """Collect a rock sample."""
        sample = {
            "id": sample_id,
            "type": rock_type,
            "position": tuple(self.position),
            "timestamp": len(self.state_history),
        }
        self.samples_collected.append(sample)
        self.battery -= 2.0  # gripper operation uses power
        return sample

    def get_state(self) -> Dict:
        """Get current rover state."""
        return {
            "position": tuple(self.position),
            "orientation": self.orientation,
            "velocity": tuple(self.velocity),
            "battery": self.battery,
            "samples_collected": len(self.samples_collected),
        }

    def _record_state(self):
        """Record state for analysis."""
        self.state_history.append(self.get_state())

    def is_operational(self) -> bool:
        """Check if rover is operational."""
        return self.battery > 5.0

    def reset_position(self, position: Tuple[float, float]):
        """Reset rover to new position."""
        self.position = np.array(position, dtype=np.float32)
        self._record_state()
