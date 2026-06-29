"""Environmental sensor data analysis using scikit-learn.

Processes multi-sensor environmental data for lunar exploration:
- Temperature, humidity, pressure
- Air quality (light absorbance/scattering)
- Cosmic radiation
- Electrical conductivity
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from typing import Dict, List, Tuple


class EnvironmentalSensorData:
    """Represents multi-sensor environmental readings."""

    def __init__(self, location_id: str, timestamp: float):
        """Initialize sensor data container."""
        self.location_id = location_id
        self.timestamp = timestamp

        # Environmental sensors
        self.temperature_c = 0.0  # Celsius
        self.humidity_percent = 0.0  # % relative humidity
        self.pressure_pa = 0.0  # Pascals
        self.air_quality_absorbance = 0.0  # Light absorbance (0-1)
        self.air_quality_scattering = 0.0  # Light scattering (0-1)
        self.cosmic_radiation_mrem = 0.0  # mrem/hour
        self.ec_conductivity_us_cm = 0.0  # microsiemens/cm (regolith conductivity)

    def to_array(self) -> np.ndarray:
        """Convert to feature array for ML."""
        return np.array([
            self.temperature_c,
            self.humidity_percent,
            self.pressure_pa / 1000,  # Normalize to kPa
            self.air_quality_absorbance,
            self.air_quality_scattering,
            self.cosmic_radiation_mrem,
            self.ec_conductivity_us_cm,
        ])

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "location_id": self.location_id,
            "timestamp": self.timestamp,
            "temperature_c": self.temperature_c,
            "humidity_percent": self.humidity_percent,
            "pressure_pa": self.pressure_pa,
            "air_quality_absorbance": self.air_quality_absorbance,
            "air_quality_scattering": self.air_quality_scattering,
            "cosmic_radiation_mrem": self.cosmic_radiation_mrem,
            "ec_conductivity_us_cm": self.ec_conductivity_us_cm,
        }


class EnvironmentalMonitor:
    """Real-time environmental monitoring and hazard detection."""

    def __init__(self):
        """Initialize environmental monitor."""
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.hazard_classifier = None
        self.data_history = []
        self._train_anomaly_detector()
        self._train_hazard_classifier()

    def _train_anomaly_detector(self):
        """Train anomaly detector on synthetic data."""
        X_train = np.random.randn(100, 7)
        self.anomaly_detector.fit(X_train)

    def _train_hazard_classifier(self):
        """Train classifier for safe/hazardous environment detection."""
        # Generate synthetic training data
        n_samples = 200
        X_train = np.random.randn(n_samples, 7)

        # Synthetic labels: safe (0) or hazardous (1)
        y_train = np.zeros(n_samples)

        # Mark high temperature, radiation as hazardous
        for i in range(n_samples):
            if X_train[i, 0] > 1.5 or X_train[i, 5] > 1.5:  # temp or radiation
                y_train[i] = 1

        self.hazard_classifier = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(n_estimators=50, random_state=42))
        ])
        self.hazard_classifier.fit(X_train, y_train)

    def assess_environment(self, sensor_data: EnvironmentalSensorData) -> Dict:
        """Assess environmental conditions at location."""
        self.data_history.append(sensor_data)

        # Get feature array
        features = sensor_data.to_array().reshape(1, -1)

        # Scale features
        features_scaled = self.scaler.fit_transform(features)

        # Detect anomalies
        anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
        is_anomaly = self.anomaly_detector.predict(features_scaled)[0] == -1

        # Classify as safe or hazardous
        hazard_prob = self.hazard_classifier.predict_proba(features_scaled)[0]

        # Safety assessment
        assessment = {
            "location_id": sensor_data.location_id,
            "timestamp": sensor_data.timestamp,
            "sensors": sensor_data.to_dict(),
            "anomaly_detected": bool(is_anomaly),
            "anomaly_score": float(anomaly_score),
            "is_safe": hazard_prob[0] > 0.5,
            "hazard_probability": float(hazard_prob[1]),
            "safety_score": float(hazard_prob[0]),
            "recommendations": self._generate_recommendations(sensor_data, hazard_prob[1]),
        }

        return assessment

    def _generate_recommendations(self, sensor_data: EnvironmentalSensorData, hazard_prob: float) -> List[str]:
        """Generate safety recommendations based on sensor readings."""
        recommendations = []

        # Temperature assessment
        if sensor_data.temperature_c < -50:
            recommendations.append("CRITICAL: Extreme cold - equipment may fail")
        elif sensor_data.temperature_c > 120:
            recommendations.append("CRITICAL: Extreme heat - thermal runaway risk")
        elif sensor_data.temperature_c > 80:
            recommendations.append("WARNING: High temperature - increase cooling")

        # Radiation assessment
        if sensor_data.cosmic_radiation_mrem > 100:
            recommendations.append("CRITICAL: Extreme radiation - immediate evacuation")
        elif sensor_data.cosmic_radiation_mrem > 50:
            recommendations.append("WARNING: High radiation - reduce EVA time")
        elif sensor_data.cosmic_radiation_mrem > 20:
            recommendations.append("CAUTION: Moderate radiation detected")

        # Air quality assessment
        air_quality_score = (sensor_data.air_quality_absorbance + sensor_data.air_quality_scattering) / 2
        if air_quality_score > 0.8:
            recommendations.append("CRITICAL: Poor air quality - airlock required")
        elif air_quality_score > 0.6:
            recommendations.append("WARNING: Degraded air quality - check filters")

        # Humidity assessment
        if sensor_data.humidity_percent > 80:
            recommendations.append("CAUTION: High humidity - condensation risk")
        elif sensor_data.humidity_percent < 20:
            recommendations.append("CAUTION: Low humidity - static electricity risk")

        # Pressure assessment
        if sensor_data.pressure_pa < 50000:
            recommendations.append("WARNING: Low atmospheric pressure")

        # EC (regolith conductivity) assessment
        if sensor_data.ec_conductivity_us_cm > 5000:
            recommendations.append("INFO: High soil conductivity - possible ice or mineral deposit")

        if hazard_prob > 0.7:
            recommendations.append("ALERT: Environment classified as hazardous")

        if not recommendations:
            recommendations.append("Environment nominal - continue operations")

        return recommendations

    def correlate_sensors(self) -> Dict:
        """Analyze correlations between sensors."""
        if len(self.data_history) < 3:
            return {}

        df = pd.DataFrame([d.to_dict() for d in self.data_history])

        # Calculate correlations
        sensor_cols = [
            "temperature_c", "humidity_percent", "pressure_pa",
            "air_quality_absorbance", "air_quality_scattering",
            "cosmic_radiation_mrem", "ec_conductivity_us_cm"
        ]

        correlations = df[sensor_cols].corr()

        return {
            "correlation_matrix": correlations.to_dict(),
            "high_correlations": self._find_high_correlations(correlations),
        }

    @staticmethod
    def _find_high_correlations(corr_matrix: pd.DataFrame, threshold: float = 0.7) -> List[Dict]:
        """Find sensor pairs with high correlation."""
        high_corr = []

        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > threshold:
                    high_corr.append({
                        "sensor_1": corr_matrix.columns[i],
                        "sensor_2": corr_matrix.columns[j],
                        "correlation": float(corr_value),
                    })

        return high_corr


class SensorDataGenerator:
    """Generate realistic environmental sensor data for testing."""

    @staticmethod
    def generate_dataset(n_locations: int = 10, n_samples_per_location: int = 5) -> List[EnvironmentalSensorData]:
        """Generate synthetic sensor data for multiple locations."""
        data = []

        for loc_idx in range(n_locations):
            location_id = f"LOC-{loc_idx:03d}"

            # Base conditions for this location
            base_temp = np.random.uniform(-40, 120)
            base_humidity = np.random.uniform(10, 60)
            base_radiation = np.random.uniform(5, 100)
            base_ec = np.random.uniform(100, 5000)

            for sample_idx in range(n_samples_per_location):
                sensor = EnvironmentalSensorData(location_id, float(loc_idx * 1000 + sample_idx))

                # Add realistic variations
                sensor.temperature_c = base_temp + np.random.normal(0, 5)
                sensor.humidity_percent = base_humidity + np.random.normal(0, 3)
                sensor.pressure_pa = 101325 + np.random.normal(0, 5000)  # Earth pressure baseline
                sensor.air_quality_absorbance = np.random.uniform(0, 0.8)
                sensor.air_quality_scattering = np.random.uniform(0, 0.8)
                sensor.cosmic_radiation_mrem = base_radiation + np.random.normal(0, 10)
                sensor.ec_conductivity_us_cm = base_ec + np.random.normal(0, 200)

                data.append(sensor)

        return data

    @staticmethod
    def generate_hazardous_event(location_id: str, timestamp: float) -> EnvironmentalSensorData:
        """Generate a hazardous environmental event."""
        sensor = EnvironmentalSensorData(location_id, timestamp)

        # Extreme conditions
        sensor.temperature_c = np.random.uniform(130, 150)  # Extreme heat
        sensor.humidity_percent = np.random.uniform(0, 15)  # Very dry
        sensor.pressure_pa = np.random.uniform(80000, 120000)
        sensor.air_quality_absorbance = np.random.uniform(0.7, 0.95)  # Poor air quality
        sensor.air_quality_scattering = np.random.uniform(0.7, 0.95)
        sensor.cosmic_radiation_mrem = np.random.uniform(75, 150)  # High radiation
        sensor.ec_conductivity_us_cm = np.random.uniform(3000, 6000)

        return sensor


class EnvironmentalLocationRanker:
    """Rank locations based on environmental suitability for missions."""

    def __init__(self):
        """Initialize location ranker."""
        self.value_predictor = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", RandomForestRegressor(n_estimators=50, random_state=42))
        ])
        self._train_value_predictor()

    def _train_value_predictor(self):
        """Train model to predict location suitability value."""
        # Synthetic training data
        n_samples = 300
        X_train = np.random.randn(n_samples, 7)

        # Suitability score (0-1): prefer moderate conditions
        y_train = np.ones(n_samples) * 0.7

        # Penalize extreme conditions
        for i in range(n_samples):
            # High temperature penalty
            if abs(X_train[i, 0]) > 2:
                y_train[i] -= 0.1 * abs(X_train[i, 0])

            # High radiation penalty
            if abs(X_train[i, 5]) > 1.5:
                y_train[i] -= 0.15 * abs(X_train[i, 5])

            # Poor air quality penalty
            if X_train[i, 3] > 1.5 or X_train[i, 4] > 1.5:
                y_train[i] -= 0.1

        y_train = np.clip(y_train, 0, 1)

        self.value_predictor.fit(X_train, y_train)

    def predict_suitability(self, sensor_data: EnvironmentalSensorData) -> float:
        """Predict environmental suitability for operations (0-1)."""
        features = sensor_data.to_array().reshape(1, -1)
        suitability = self.value_predictor.predict(features)[0]
        return float(np.clip(suitability, 0, 1))

    def rank_locations(self, location_data: List[Dict]) -> List[Dict]:
        """Rank multiple locations by environmental suitability."""
        ranked = []

        for loc_data in location_data:
            sensor = EnvironmentalSensorData(loc_data["id"], loc_data.get("timestamp", 0))
            sensor.temperature_c = loc_data.get("temperature_c", 0)
            sensor.humidity_percent = loc_data.get("humidity_percent", 50)
            sensor.pressure_pa = loc_data.get("pressure_pa", 101325)
            sensor.air_quality_absorbance = loc_data.get("air_quality_absorbance", 0.3)
            sensor.air_quality_scattering = loc_data.get("air_quality_scattering", 0.3)
            sensor.cosmic_radiation_mrem = loc_data.get("cosmic_radiation_mrem", 20)
            sensor.ec_conductivity_us_cm = loc_data.get("ec_conductivity_us_cm", 1000)

            suitability = self.predict_suitability(sensor)

            ranked.append({
                "location_id": loc_data["id"],
                "environmental_suitability": suitability,
                "sensor_data": sensor.to_dict(),
            })

        # Sort by suitability (descending)
        ranked.sort(key=lambda x: x["environmental_suitability"], reverse=True)
        return ranked


class SensorClusterAnalysis:
    """Cluster locations based on environmental similarity."""

    @staticmethod
    def cluster_by_environment(location_data: List[Dict], n_clusters: int = 3) -> Dict[int, List[Dict]]:
        """Group locations with similar environmental conditions."""
        if not location_data:
            return {}

        # Extract features
        features = []
        for loc in location_data:
            sensor = EnvironmentalSensorData(loc["id"], loc.get("timestamp", 0))
            sensor.temperature_c = loc.get("temperature_c", 0)
            sensor.humidity_percent = loc.get("humidity_percent", 50)
            sensor.pressure_pa = loc.get("pressure_pa", 101325)
            sensor.air_quality_absorbance = loc.get("air_quality_absorbance", 0.3)
            sensor.air_quality_scattering = loc.get("air_quality_scattering", 0.3)
            sensor.cosmic_radiation_mrem = loc.get("cosmic_radiation_mrem", 20)
            sensor.ec_conductivity_us_cm = loc.get("ec_conductivity_us_cm", 1000)

            features.append(sensor.to_array())

        X = np.array(features)

        # Scale and cluster
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        kmeans = KMeans(n_clusters=min(n_clusters, len(location_data)), random_state=42)
        clusters = kmeans.fit_predict(X_scaled)

        # Group by cluster
        grouped = {}
        for idx, cluster_id in enumerate(clusters):
            if cluster_id not in grouped:
                grouped[cluster_id] = []
            grouped[cluster_id].append({**location_data[idx], "cluster": cluster_id})

        return grouped


def demonstrate_environmental_analysis():
    """Show environmental monitoring capabilities."""
    print("\n" + "="*70)
    print("ENVIRONMENTAL SENSOR DATA ANALYSIS")
    print("="*70 + "\n")

    # Generate test data
    print("1. Generating synthetic sensor data...")
    data = SensorDataGenerator.generate_dataset(n_locations=5, n_samples_per_location=3)
    print(f"   Generated {len(data)} sensor readings\n")

    # Monitor environments
    print("2. Assessing environmental conditions...")
    monitor = EnvironmentalMonitor()

    safe_count = 0
    hazardous_count = 0

    for sensor_data in data[:5]:
        assessment = monitor.assess_environment(sensor_data)
        if assessment["is_safe"]:
            safe_count += 1
        else:
            hazardous_count += 1

        if "LOC-000" in sensor_data.location_id:
            print(f"\n   Location: {assessment['location_id']}")
            print(f"   Temperature: {sensor_data.temperature_c:.1f}°C")
            print(f"   Cosmic Radiation: {sensor_data.cosmic_radiation_mrem:.1f} mrem/h")
            print(f"   Air Quality: {(sensor_data.air_quality_absorbance + sensor_data.air_quality_scattering)/2:.2f}")
            print(f"   Safe: {assessment['is_safe']}")
            print(f"   Hazard Probability: {assessment['hazard_probability']:.2%}")

    print(f"\n   Safe locations: {safe_count}")
    print(f"   Hazardous locations: {hazardous_count}\n")

    # Rank locations
    print("3. Ranking locations by environmental suitability...")
    location_data = [
        {"id": "LOC-A", "temperature_c": 20, "humidity_percent": 50, "cosmic_radiation_mrem": 15},
        {"id": "LOC-B", "temperature_c": 100, "humidity_percent": 30, "cosmic_radiation_mrem": 80},
        {"id": "LOC-C", "temperature_c": 50, "humidity_percent": 45, "cosmic_radiation_mrem": 30},
    ]

    ranker = EnvironmentalLocationRanker()
    ranked = ranker.rank_locations(location_data)

    for i, loc in enumerate(ranked, 1):
        print(f"   {i}. {loc['location_id']}: {loc['environmental_suitability']:.2%} suitability")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    demonstrate_environmental_analysis()
