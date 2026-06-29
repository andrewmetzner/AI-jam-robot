"""
MuJoCo simulation interface for robotic arm control
"""

import mujoco
import numpy as np
from pathlib import Path


class MuJoCoSimulator:
    def __init__(self, scene_path: str, headless: bool = False):
        """Initialize MuJoCo simulator with a given scene."""
        scene_path = Path(scene_path)
        if not scene_path.is_absolute():
            scene_path = Path(__file__).parent / scene_path
        self.scene_path = str(scene_path)
        self.headless = headless
        self.model = None
        self.data = None
        self.renderer = None
        self.load_scene()

    def load_scene(self):
        """Load MuJoCo XML scene file."""
        try:
            self.model = mujoco.MjModel.from_xml_path(self.scene_path)
            self.data = mujoco.MjData(self.model)
            print(f"Loaded scene: {self.scene_path}")
        except Exception as e:
            print(f"Error loading scene: {e}")

    def step(self, action: np.ndarray, duration: float = 0.01):
        """Step simulation with given action."""
        if self.model is None or self.data is None:
            return
        if len(action) == self.model.nu:
            self.data.ctrl[:] = action
        mujoco.mj_step(self.model, self.data, int(duration / self.model.opt.timestep))

    def get_state(self) -> dict:
        """Get current robot state."""
        return {
            "qpos": self.data.qpos.copy(),
            "qvel": self.data.qvel.copy(),
            "time": self.data.time,
        }

    def set_state(self, qpos: np.ndarray):
        """Set robot joint positions."""
        self.data.qpos[:] = qpos
        mujoco.mj_forward(self.model, self.data)

    def get_body_pos(self, body_name: str) -> np.ndarray:
        """Get position of named body."""
        if self.model is None:
            return None
        body_id = mujoco.mj_name2id(self.model, 1, body_name)
        if body_id >= 0:
            return self.data.xpos[body_id].copy()
        return None

    def render(self):
        """Render simulation frame."""
        if not self.headless and self.renderer is None:
            self.renderer = mujoco.Renderer(self.model)
        if self.renderer:
            self.renderer.update_scene(self.data)
            pixels = self.renderer.render()
            return pixels

    def close(self):
        """Clean up resources."""
        if self.renderer:
            self.renderer.close()
