"""Environmental data fusion with rover decision-making systems.

Integrates environmental sensor readings with:
- Route planning (avoid hazardous zones)
- Sample prioritization (environmental context)
- Astronaut safety (real-time hazard assessment)
- Mission planning (environmental windows)
"""

import numpy as np
from typing import Dict, List, Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor


class EnvironmentalFusionEngine:
    """Fuse environmental data with rover decision systems."""

    def __init__(self):
        """Initialize fusion engine."""
        self.scaler = StandardScaler()
        self.risk_model = GradientBoostingRegressor(n_estimators=50, random_state=42)
        self._train_risk_model()
        self.hazard_map = {}
        self.safe_zones = {}

    def _train_risk_model(self):
        """Train model to predict traversal risk based on environment."""
        n_samples = 300
        X_train = np.random.randn(n_samples, 8)

        # Risk score: 0 = safe, 1 = extreme hazard
        y_train = np.zeros(n_samples)

        for i in range(n_samples):
            # Temperature extremes increase risk
            if abs(X_train[i, 0]) > 2:
                y_train[i] += 0.1 * abs(X_train[i, 0])

            # Radiation increases risk
            if X_train[i, 5] > 1.5:
                y_train[i] += 0.2 * X_train[i, 5]

            # Poor air quality increases risk
            if X_train[i, 3] > 1.0 or X_train[i, 4] > 1.0:
                y_train[i] += 0.15

            # High terrain slope increases risk
            if X_train[i, 7] > 2:
                y_train[i] += 0.1 * X_train[i, 7]

        y_train = np.clip(y_train, 0, 1)
        self.risk_model.fit(X_train, y_train)

    def assess_traversal_risk(
        self,
        temperature: float,
        humidity: float,
        pressure: float,
        air_quality: float,
        radiation: float,
        ec: float,
        terrain_slope: float = 0.0
    ) -> Dict:
        """Assess risk for rover traversal at location."""
        # Normalize features
        features = np.array([[
            temperature,
            humidity,
            pressure / 1000,
            air_quality,
            air_quality,  # Combined air quality
            radiation,
            ec / 1000,
            terrain_slope,
        ]])

        risk_score = self.risk_model.predict(features)[0]
        risk_score = np.clip(risk_score, 0, 1)

        # Generate risk classification
        if risk_score > 0.8:
            risk_level = "EXTREME"
            action = "AVOID_ZONE"
        elif risk_score > 0.6:
            risk_level = "HIGH"
            action = "REDUCED_SPEED"
        elif risk_score > 0.4:
            risk_level = "MODERATE"
            action = "CAUTION"
        elif risk_score > 0.2:
            risk_level = "LOW"
            action = "PROCEED"
        else:
            risk_level = "MINIMAL"
            action = "OPTIMAL"

        return {
            "risk_score": float(risk_score),
            "risk_level": risk_level,
            "recommended_action": action,
            "traversal_safe": risk_score < 0.6,
            "max_speed_percent": int(100 * (1 - risk_score)),
        }

    def create_hazard_map(self, locations: List[Dict]) -> Dict[str, Dict]:
        """Create spatial hazard map from environmental data."""
        hazard_map = {}

        for loc in locations:
            loc_id = loc["id"]

            risk = self.assess_traversal_risk(
                temperature=loc.get("temperature_c", 0),
                humidity=loc.get("humidity_percent", 50),
                pressure=loc.get("pressure_pa", 101325),
                air_quality=(loc.get("air_quality_absorbance", 0.3) +
                           loc.get("air_quality_scattering", 0.3)) / 2,
                radiation=loc.get("cosmic_radiation_mrem", 20),
                ec=loc.get("ec_conductivity_us_cm", 1000),
                terrain_slope=loc.get("terrain_slope", 0),
            )

            hazard_map[loc_id] = {
                "location": loc_id,
                "risk": risk,
                "coordinates": (loc.get("x", 0), loc.get("y", 0)),
            }

        self.hazard_map = hazard_map
        return hazard_map

    def identify_safe_zones(self, locations: List[Dict], safety_threshold: float = 0.4) -> List[str]:
        """Identify safe zones for rover operations."""
        safe_zones = []

        for loc in locations:
            risk = self.assess_traversal_risk(
                temperature=loc.get("temperature_c", 0),
                humidity=loc.get("humidity_percent", 50),
                pressure=loc.get("pressure_pa", 101325),
                air_quality=(loc.get("air_quality_absorbance", 0.3) +
                           loc.get("air_quality_scattering", 0.3)) / 2,
                radiation=loc.get("cosmic_radiation_mrem", 20),
                ec=loc.get("ec_conductivity_us_cm", 1000),
            )

            if risk["risk_score"] < safety_threshold:
                safe_zones.append(loc["id"])

        self.safe_zones = {zone: True for zone in safe_zones}
        return safe_zones

    def predict_environmental_window(
        self,
        current_conditions: Dict,
        forecast_conditions: List[Dict]
    ) -> Dict:
        """Predict optimal time window for operations based on forecast."""
        current_risk = self.assess_traversal_risk(
            temperature=current_conditions.get("temperature_c", 0),
            humidity=current_conditions.get("humidity_percent", 50),
            pressure=current_conditions.get("pressure_pa", 101325),
            air_quality=(current_conditions.get("air_quality_absorbance", 0.3) +
                       current_conditions.get("air_quality_scattering", 0.3)) / 2,
            radiation=current_conditions.get("cosmic_radiation_mrem", 20),
            ec=current_conditions.get("ec_conductivity_us_cm", 1000),
        )

        window_scores = []
        for i, conditions in enumerate(forecast_conditions):
            risk = self.assess_traversal_risk(
                temperature=conditions.get("temperature_c", 0),
                humidity=conditions.get("humidity_percent", 50),
                pressure=conditions.get("pressure_pa", 101325),
                air_quality=(conditions.get("air_quality_absorbance", 0.3) +
                           conditions.get("air_quality_scattering", 0.3)) / 2,
                radiation=conditions.get("cosmic_radiation_mrem", 20),
                ec=conditions.get("ec_conductivity_us_cm", 1000),
            )

            window_scores.append({
                "time_index": i,
                "risk_score": risk["risk_score"],
                "risk_level": risk["risk_level"],
            })

        # Find best window
        best_window = min(window_scores, key=lambda x: x["risk_score"])
        worst_windows = [w for w in window_scores if w["risk_level"] == "EXTREME"]

        return {
            "current_risk": current_risk["risk_score"],
            "best_window": best_window,
            "optimal_time_index": best_window["time_index"],
            "hazardous_periods": worst_windows,
            "recommendation": self._generate_window_recommendation(current_risk, best_window),
        }

    @staticmethod
    def _generate_window_recommendation(current_risk: Dict, best_window: Dict) -> str:
        """Generate recommendation for operation timing."""
        if best_window["risk_level"] == "EXTREME":
            return "Wait for better conditions - current forecast shows extreme risk"
        elif best_window["risk_level"] == "HIGH":
            return "Operations possible but proceed with caution"
        elif current_risk["risk_level"] == "MINIMAL":
            return "Begin operations immediately - conditions are optimal"
        else:
            return f"Operate at time index {best_window['time_index']} for best conditions"


class SampleContextAnalyzer:
    """Analyze samples in environmental context."""

    def __init__(self):
        """Initialize analyzer."""
        self.context_model = GradientBoostingRegressor(n_estimators=50, random_state=42)
        self._train_context_model()

    def _train_context_model(self):
        """Train model for sample value in environmental context."""
        n_samples = 300
        X_train = np.random.randn(n_samples, 7)
        y_train = np.random.uniform(0.3, 1.0, n_samples)

        # Samples in moderate conditions are more valuable
        for i in range(n_samples):
            if abs(X_train[i, 0]) < 1:  # Moderate temperature
                y_train[i] += 0.1
            if abs(X_train[i, 5]) < 1:  # Moderate radiation
                y_train[i] += 0.1

        y_train = np.clip(y_train, 0, 1)
        self.context_model.fit(X_train, y_train)

    def assess_sample_value_in_context(
        self,
        sample: Dict,
        environmental_conditions: Dict
    ) -> Dict:
        """Assess sample scientific value adjusted for environmental context."""
        # Environmental context features
        context_features = np.array([[
            environmental_conditions.get("temperature_c", 0),
            environmental_conditions.get("humidity_percent", 50),
            environmental_conditions.get("pressure_pa", 101325) / 1000,
            environmental_conditions.get("air_quality_absorbance", 0.3),
            environmental_conditions.get("air_quality_scattering", 0.3),
            environmental_conditions.get("cosmic_radiation_mrem", 20),
            environmental_conditions.get("ec_conductivity_us_cm", 1000) / 1000,
        ]])

        context_value = self.context_model.predict(context_features)[0]

        # Base sample value
        base_value = sample.get("base_value", 0.7)

        # Adjust for environmental context
        adjusted_value = base_value * (0.5 + 0.5 * context_value)

        # Environmental context affects collection strategy
        if environmental_conditions.get("cosmic_radiation_mrem", 20) > 50:
            adjusted_value *= 1.1  # Higher value in high-radiation zones (rarity)
            collection_strategy = "PRIORITY_COLLECTION"
        else:
            collection_strategy = "STANDARD_COLLECTION"

        return {
            "sample_id": sample.get("id"),
            "base_value": base_value,
            "context_adjustment": context_value,
            "adjusted_value": float(adjusted_value),
            "collection_strategy": collection_strategy,
            "environmental_conditions": environmental_conditions,
        }


class CriticalEventDetector:
    """Detect critical environmental events."""

    @staticmethod
    def detect_thermal_anomaly(temperature: float, baseline: float = 20.0, threshold: float = 30.0) -> bool:
        """Detect extreme temperature deviation."""
        return abs(temperature - baseline) > threshold

    @staticmethod
    def detect_radiation_spike(radiation: float, threshold: float = 80.0) -> bool:
        """Detect high radiation event."""
        return radiation > threshold

    @staticmethod
    def detect_air_quality_degradation(
        absorbance: float,
        scattering: float,
        threshold: float = 0.7
    ) -> bool:
        """Detect poor air quality."""
        air_quality = (absorbance + scattering) / 2
        return air_quality > threshold

    @staticmethod
    def detect_pressure_anomaly(pressure: float, baseline: float = 101325, threshold: float = 20000) -> bool:
        """Detect atmospheric pressure anomaly."""
        return abs(pressure - baseline) > threshold

    @staticmethod
    def check_all_critical_conditions(
        temperature: float,
        radiation: float,
        air_quality_abs: float,
        air_quality_scat: float,
        pressure: float,
    ) -> Dict:
        """Check all critical conditions simultaneously."""
        events = []

        if CriticalEventDetector.detect_thermal_anomaly(temperature):
            events.append("THERMAL_ANOMALY")

        if CriticalEventDetector.detect_radiation_spike(radiation):
            events.append("RADIATION_SPIKE")

        if CriticalEventDetector.detect_air_quality_degradation(air_quality_abs, air_quality_scat):
            events.append("AIR_QUALITY_DEGRADATION")

        if CriticalEventDetector.detect_pressure_anomaly(pressure):
            events.append("PRESSURE_ANOMALY")

        return {
            "critical_events": events,
            "event_count": len(events),
            "is_critical": len(events) > 0,
            "action": "EMERGENCY_RETURN_TO_BASE" if len(events) > 2 else "PROCEED_WITH_CAUTION",
        }


def demonstrate_environmental_fusion():
    """Demonstrate environmental fusion capabilities."""
    print("\n" + "="*70)
    print("ENVIRONMENTAL FUSION ENGINE DEMONSTRATION")
    print("="*70 + "\n")

    fusion = EnvironmentalFusionEngine()

    # Test traversal risk assessment
    print("1. Traversal Risk Assessment:")
    test_locations = [
        {"id": "LOC-SAFE", "temperature_c": 20, "humidity_percent": 50, "cosmic_radiation_mrem": 15},
        {"id": "LOC-HAZARD", "temperature_c": 120, "humidity_percent": 30, "cosmic_radiation_mrem": 90},
    ]

    for loc in test_locations:
        risk = fusion.assess_traversal_risk(
            temperature=loc["temperature_c"],
            humidity=loc["humidity_percent"],
            pressure=101325,
            air_quality=0.3,
            radiation=loc["cosmic_radiation_mrem"],
            ec=1000,
        )
        print(f"\n   {loc['id']}:")
        print(f"     Risk: {risk['risk_level']} ({risk['risk_score']:.2%})")
        print(f"     Action: {risk['recommended_action']}")
        print(f"     Max Speed: {risk['max_speed_percent']}%")

    # Test safe zones
    print("\n\n2. Safe Zone Identification:")
    safe_zones = fusion.identify_safe_zones(test_locations)
    print(f"   Safe zones: {safe_zones if safe_zones else 'None'}")

    # Test critical event detection
    print("\n\n3. Critical Event Detection:")
    events = CriticalEventDetector.check_all_critical_conditions(
        temperature=140,
        radiation=100,
        air_quality_abs=0.8,
        air_quality_scat=0.8,
        pressure=80000,
    )
    print(f"   Events detected: {events['critical_events']}")
    print(f"   Recommended action: {events['action']}")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    demonstrate_environmental_fusion()
