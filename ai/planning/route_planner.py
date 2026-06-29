"""Route planning for autonomous navigation."""

from typing import List, Tuple, Dict
import numpy as np


class RoutePlanner:
    def __init__(self, grid_size: Tuple[int, int] = (100, 100)):
        """Initialize route planner."""
        self.grid_size = grid_size
        self.occupancy_grid = np.zeros(grid_size)
        self.paths = []

    def plan_route(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        obstacles: List[Dict] = None,
    ) -> List[Tuple[float, float]]:
        """
        Plan a collision-free route using A* algorithm.
        """
        if obstacles:
            self._update_occupancy_grid(obstacles)

        # Simple A* implementation
        path = self._astar(start, goal)
        self.paths.append(path)
        return path

    def _astar(
        self, start: Tuple[float, float], goal: Tuple[float, float]
    ) -> List[Tuple[float, float]]:
        """A* path planning algorithm."""
        path = [start]

        current = np.array(start, dtype=np.float32)
        goal = np.array(goal, dtype=np.float32)
        step_size = 0.5

        while np.linalg.norm(current - goal) > step_size:
            direction = goal - current
            direction = direction / np.linalg.norm(direction)
            next_pos = current + direction * step_size

            # Check for collisions
            if not self._is_collision(tuple(next_pos)):
                current = next_pos
                path.append(tuple(current))
            else:
                # Simple obstacle avoidance: try perpendicular direction
                perp_dir = np.array([-direction[1], direction[0]])
                next_pos = current + perp_dir * step_size
                if not self._is_collision(tuple(next_pos)):
                    current = next_pos
                    path.append(tuple(current))
                else:
                    break

        path.append(tuple(goal))
        return path

    def _update_occupancy_grid(self, obstacles: List[Dict]):
        """Update occupancy grid with obstacle information."""
        self.occupancy_grid.fill(0)

        for obstacle in obstacles:
            if obstacle["type"] == "depth_obstacle":
                # Mark grid cells as occupied
                min_safe = int(obstacle.get("min_distance", 0.5) * 10)
                self.occupancy_grid[:min_safe, :] = 1

    def _is_collision(self, pos: Tuple[float, float]) -> bool:
        """Check if position is collision-free."""
        x, y = int(pos[0]), int(pos[1])
        if 0 <= x < self.grid_size[0] and 0 <= y < self.grid_size[1]:
            return self.occupancy_grid[x, y] > 0.5
        return False

    def get_latest_path(self) -> List[Tuple[float, float]]:
        """Get the latest planned path."""
        return self.paths[-1] if self.paths else []

    def smooth_path(self, path: List[Tuple[float, float]], smoothing: int = 3) -> List[Tuple[float, float]]:
        """Apply smoothing to path using moving average."""
        if len(path) < smoothing:
            return path

        smoothed = []
        for i in range(len(path)):
            start_idx = max(0, i - smoothing // 2)
            end_idx = min(len(path), i + smoothing // 2 + 1)
            avg_x = np.mean([p[0] for p in path[start_idx:end_idx]])
            avg_y = np.mean([p[1] for p in path[start_idx:end_idx]])
            smoothed.append((avg_x, avg_y))

        return smoothed
