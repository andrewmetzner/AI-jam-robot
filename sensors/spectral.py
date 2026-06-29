"""Simulated spectral analyzer for rock composition."""

import numpy as np


class SpectralAnalyzer:
    def __init__(self):
        """Initialize spectral analyzer."""
        self.spectrum = None
        self.rock_types = {
            "basalt": {"Fe": 0.15, "Mg": 0.12, "Si": 0.25, "Ca": 0.08, "Al": 0.10},
            "olivine": {"Mg": 0.30, "Fe": 0.20, "Si": 0.18, "Ca": 0.02},
            "anorthosite": {"Al": 0.25, "Si": 0.28, "Ca": 0.15, "Mg": 0.05},
            "regolith": {"Si": 0.22, "Fe": 0.08, "Mg": 0.08, "Al": 0.12, "O": 0.20},
        }

    def analyze(self, scene_data: dict) -> dict:
        """Analyze spectrum of observed rock."""
        if "spectrum" in scene_data:
            self.spectrum = scene_data["spectrum"]
        else:
            self.spectrum = self._simulate_spectrum()

        composition = self._infer_composition(self.spectrum)
        return composition

    def _simulate_spectrum(self) -> dict:
        """Simulate spectral data for random rock type."""
        rock_type = np.random.choice(list(self.rock_types.keys()))
        base_comp = self.rock_types[rock_type]
        noise = {k: v + np.random.normal(0, 0.02) for k, v in base_comp.items()}
        return {k: max(0, v) for k, v in noise.items()}

    def _infer_composition(self, spectrum: dict) -> dict:
        """Infer rock type from spectral data."""
        scores = {}
        for rock_type, expected in self.rock_types.items():
            diff = sum(abs(spectrum.get(k, 0) - v) for k, v in expected.items())
            scores[rock_type] = 1.0 / (1.0 + diff)

        best_match = max(scores.items(), key=lambda x: x[1])
        return {
            "rock_type": best_match[0],
            "confidence": best_match[1],
            "composition": spectrum,
            "elements": list(spectrum.keys()),
        }

    def get_spectrum(self) -> dict:
        """Get latest spectral data."""
        return self.spectrum
