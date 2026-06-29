"""Machine learning models using scikit-learn for enhanced autonomous reasoning."""

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from typing import Dict, List, Tuple


class RockTypeClassifier:
    """ML-based rock type classification using scikit-learn."""

    def __init__(self):
        """Initialize the rock classifier."""
        self.rock_types = ["basalt", "olivine", "anorthosite", "regolith"]
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(n_estimators=50, random_state=42))
        ])
        self._train_model()

    def _train_model(self):
        """Train classifier on synthetic training data."""
        # Synthetic training data (features: visual_confidence, spectral_features, etc)
        X_train = self._generate_training_data(n_samples=200)
        y_train = np.repeat(self.rock_types, 50)  # 50 samples per rock type

        self.model.fit(X_train, y_train)

    def _generate_training_data(self, n_samples: int = 200) -> np.ndarray:
        """Generate synthetic training features."""
        features = []

        for rock_type_idx, rock_type in enumerate(self.rock_types):
            # Generate synthetic features for each rock type
            if rock_type == "basalt":
                Fe = np.random.normal(0.15, 0.03, n_samples // 4)
                Mg = np.random.normal(0.12, 0.02, n_samples // 4)
                Si = np.random.normal(0.25, 0.04, n_samples // 4)
            elif rock_type == "olivine":
                Fe = np.random.normal(0.20, 0.04, n_samples // 4)
                Mg = np.random.normal(0.30, 0.05, n_samples // 4)
                Si = np.random.normal(0.18, 0.03, n_samples // 4)
            elif rock_type == "anorthosite":
                Fe = np.random.normal(0.05, 0.02, n_samples // 4)
                Al = np.random.normal(0.25, 0.04, n_samples // 4)
                Si = np.random.normal(0.28, 0.04, n_samples // 4)
            else:  # regolith
                Fe = np.random.normal(0.08, 0.03, n_samples // 4)
                Si = np.random.normal(0.22, 0.04, n_samples // 4)
                Mg = np.random.normal(0.08, 0.02, n_samples // 4)

            visual_confidence = np.random.normal(0.80, 0.10, n_samples // 4)
            spectral_confidence = np.random.normal(0.75, 0.12, n_samples // 4)

            rock_features = np.column_stack([Fe, Mg, Si, visual_confidence, spectral_confidence])
            features.append(rock_features)

        return np.vstack(features)

    def predict(self, sample_features) -> Tuple[str, float]:
        """Predict rock type and confidence."""
        # Convert to numpy array if needed
        if not isinstance(sample_features, np.ndarray):
            sample_features = np.array(sample_features)

        if sample_features.ndim == 1:
            sample_features = sample_features.reshape(1, -1)

        prediction = self.model.predict(sample_features)[0]
        confidence = self.model.predict_proba(sample_features).max()

        return prediction, confidence

    def predict_batch(self, samples: List[Dict]) -> List[Dict]:
        """Predict rock types for multiple samples."""
        results = []

        for sample in samples:
            # Extract features from sample
            features = np.array([
                sample.get("Fe", 0.1),
                sample.get("Mg", 0.1),
                sample.get("Si", 0.2),
                sample.get("visual_confidence", 0.7),
                sample.get("spectral_confidence", 0.7),
            ])

            rock_type, confidence = self.predict(features)
            results.append({
                "sample_id": sample.get("id"),
                "predicted_type": rock_type,
                "confidence": float(confidence),
            })

        return results


class SampleValuePredictor:
    """ML regression model to predict scientific value of samples."""

    def __init__(self):
        """Initialize the value predictor."""
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", GradientBoostingRegressor(n_estimators=50, random_state=42))
        ])
        self._train_model()

    def _train_model(self):
        """Train regressor on synthetic data."""
        X_train = self._generate_training_data(n_samples=300)
        y_train = np.random.uniform(0.3, 1.0, 300)  # Value scores 0-1

        self.model.fit(X_train, y_train)

    def _generate_training_data(self, n_samples: int) -> np.ndarray:
        """Generate synthetic training features."""
        visual_confidence = np.random.uniform(0.5, 1.0, n_samples)
        spectral_confidence = np.random.uniform(0.5, 1.0, n_samples)
        rock_rarity = np.random.uniform(0.0, 1.0, n_samples)  # 0=common, 1=rare
        accessibility = np.random.uniform(0.0, 1.0, n_samples)  # 0=hard, 1=easy
        depth = np.random.uniform(0.0, 3.0, n_samples)  # meters below surface

        return np.column_stack([
            visual_confidence,
            spectral_confidence,
            rock_rarity,
            accessibility,
            depth,
        ])

    def predict_value(self, sample: Dict) -> float:
        """Predict scientific value of a sample (0-1)."""
        features = np.array([
            sample.get("visual_confidence", 0.7),
            sample.get("spectral_confidence", 0.7),
            sample.get("rarity", 0.5),
            sample.get("accessibility", 0.8),
            sample.get("depth", 0.0),
        ]).reshape(1, -1)

        value = self.model.predict(features)[0]
        return max(0.0, min(1.0, value))  # Clamp to [0, 1]

    def rank_samples(self, samples: List[Dict]) -> List[Dict]:
        """Rank samples by predicted scientific value."""
        ranked = []

        for sample in samples:
            value = self.predict_value(sample)
            ranked.append({
                "sample_id": sample.get("id"),
                "predicted_value": value,
                "rock_type": sample.get("type", "unknown"),
                "confidence": sample.get("confidence", 0.7),
            })

        # Sort by predicted value (descending)
        ranked.sort(key=lambda x: x["predicted_value"], reverse=True)
        return ranked


class SampleClustering:
    """ML-based clustering to group similar samples."""

    @staticmethod
    def cluster_by_composition(samples: List[Dict], n_clusters: int = 3) -> Dict[int, List[Dict]]:
        """Group samples by spectral composition using clustering."""
        from sklearn.cluster import KMeans

        if not samples:
            return {}

        # Extract composition features
        X = np.array([
            [
                sample.get("composition", {}).get("Fe", 0.1),
                sample.get("composition", {}).get("Mg", 0.1),
                sample.get("composition", {}).get("Si", 0.2),
                sample.get("composition", {}).get("Al", 0.1),
            ]
            for sample in samples
        ])

        # Cluster
        kmeans = KMeans(n_clusters=min(n_clusters, len(samples)), random_state=42)
        clusters = kmeans.fit_predict(X)

        # Group by cluster
        grouped = {}
        for idx, cluster_id in enumerate(clusters):
            if cluster_id not in grouped:
                grouped[cluster_id] = []
            grouped[cluster_id].append({**samples[idx], "cluster": cluster_id})

        return grouped

    @staticmethod
    def cluster_by_location(samples: List[Dict], n_clusters: int = 3) -> Dict[int, List[Dict]]:
        """Group samples by spatial location."""
        from sklearn.cluster import KMeans

        if not samples:
            return {}

        # Extract spatial features
        X = np.array([
            sample.get("position", (0, 0)) + (sample.get("depth", 0),)
            for sample in samples
        ])

        # Cluster
        kmeans = KMeans(n_clusters=min(n_clusters, len(samples)), random_state=42)
        clusters = kmeans.fit_predict(X)

        # Group by cluster
        grouped = {}
        for idx, cluster_id in enumerate(clusters):
            if cluster_id not in grouped:
                grouped[cluster_id] = []
            grouped[cluster_id].append({**samples[idx], "location_cluster": cluster_id})

        return grouped


class AnomalyDetector:
    """Detect anomalous samples that warrant special attention."""

    @staticmethod
    def detect_anomalies(samples: List[Dict], contamination: float = 0.1) -> List[Dict]:
        """Detect anomalous samples using isolation forest."""
        from sklearn.ensemble import IsolationForest

        if len(samples) < 2:
            return []

        # Extract features
        X = np.array([
            [
                sample.get("visual_confidence", 0.7),
                sample.get("spectral_confidence", 0.7),
                sample.get("confidence", 0.7),
            ]
            for sample in samples
        ])

        # Detect anomalies
        iso_forest = IsolationForest(contamination=min(contamination, 0.5), random_state=42)
        predictions = iso_forest.fit_predict(X)

        # Return anomalies
        anomalies = []
        for idx, pred in enumerate(predictions):
            if pred == -1:  # Anomaly
                anomalies.append({
                    "sample_id": samples[idx].get("id"),
                    "reason": "Unusual spectral signature detected",
                    "anomaly_score": -iso_forest.offset_ - iso_forest.score_samples(X[idx:idx+1])[0],
                })

        return anomalies


if __name__ == "__main__":
    # Test rock classifier
    print("Testing RockTypeClassifier:")
    classifier = RockTypeClassifier()
    test_sample = np.array([0.15, 0.12, 0.25, 0.85, 0.80])
    rock_type, confidence = classifier.predict(test_sample)
    print(f"  Predicted: {rock_type} (confidence: {confidence:.2%})\n")

    # Test value predictor
    print("Testing SampleValuePredictor:")
    predictor = SampleValuePredictor()
    test_sample = {
        "visual_confidence": 0.90,
        "spectral_confidence": 0.85,
        "rarity": 0.8,
        "accessibility": 0.9,
        "depth": 0.5,
    }
    value = predictor.predict_value(test_sample)
    print(f"  Predicted value: {value:.2f}\n")

    # Test clustering
    print("Testing Clustering:")
    samples = [
        {"id": i, "composition": {"Fe": 0.15, "Mg": 0.12, "Si": 0.25, "Al": 0.1}}
        for i in range(10)
    ]
    clusters = SampleClustering.cluster_by_composition(samples, n_clusters=3)
    print(f"  Clustered into {len(clusters)} groups\n")

    # Test anomaly detection
    print("Testing AnomalyDetector:")
    samples = [
        {"id": i, "visual_confidence": 0.85, "spectral_confidence": 0.80, "confidence": 0.82}
        for i in range(5)
    ]
    samples.append({"id": 5, "visual_confidence": 0.2, "spectral_confidence": 0.15, "confidence": 0.1})
    anomalies = AnomalyDetector.detect_anomalies(samples)
    print(f"  Detected {len(anomalies)} anomalies")
    for anomaly in anomalies:
        print(f"    - Sample {anomaly['sample_id']}: {anomaly['reason']}")
