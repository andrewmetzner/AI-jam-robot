"""Astronaut Health & Safety Monitoring System for Lunar EVA Operations."""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


class HealthStatus(Enum):
    """Astronaut health status levels."""
    NOMINAL = "nominal"
    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"


class SuitStatus(Enum):
    """Space suit status levels."""
    OPTIMAL = "optimal"
    DEGRADED = "degraded"
    COMPROMISED = "compromised"
    EMERGENCY = "emergency"


@dataclass
class BiometricThresholds:
    """Safe operating ranges for astronaut biometrics."""
    # Heart rate (bpm)
    heart_rate_min: int = 50
    heart_rate_max: int = 130
    heart_rate_critical: int = 150

    # Oxygen saturation (%)
    oxygen_sat_min: int = 90
    oxygen_sat_critical: int = 85

    # Core temperature (°C)
    temp_min: float = 36.5
    temp_max: float = 39.0
    temp_critical: float = 39.5

    # Blood pressure (mmHg)
    systolic_min: int = 90
    systolic_max: int = 160
    diastolic_min: int = 60
    diastolic_max: int = 100

    # CO2 levels in suit (%)
    co2_max: float = 4.0
    co2_critical: float = 6.0

    # Suit pressure (psi)
    suit_pressure_nominal: float = 4.3  # PSI
    suit_pressure_min: float = 3.8
    suit_pressure_critical: float = 3.0

    # Dust/abrasive contamination (micrograms/liter)
    dust_max: float = 5.0  # Safe threshold
    dust_critical: float = 10.0  # Return to base required


@dataclass
class AstronautBiometrics:
    """Real-time astronaut health data."""
    astronaut_id: str
    timestamp: float

    # Vital signs
    heart_rate: int  # bpm
    blood_pressure_sys: int  # mmHg
    blood_pressure_dia: int  # mmHg
    core_temperature: float  # °C
    oxygen_saturation: int  # %
    respiration_rate: int  # breaths/min

    # Suit metrics
    suit_pressure: float  # PSI
    oxygen_remaining: float  # hours
    co2_level: float  # %
    suit_integrity: float  # % (100% = intact)

    # Environmental
    ambient_dust: float  # micrograms/liter
    suit_temperature: float  # °C
    radiation_exposure: float  # mSv

    # Activity metrics
    metabolic_rate: float  # kcal/hour
    work_duration: float  # hours
    fatigue_level: float  # 0-1 (0=fresh, 1=exhausted)


@dataclass
class SpaceConditions:
    """Environmental conditions used to estimate astronaut cardiovascular load."""
    radiation_usv_h: float = 0.0
    temperature_c: float = 0.0
    suit_pressure: float = 4.3
    oxygen_saturation: int = 98
    co2_level: float = 2.8
    dust_level: float = 0.0
    metabolic_rate: float = 300.0
    fatigue_level: float = 0.0
    work_duration: float = 0.0


class AstronautMonitor:
    """Real-time health monitoring for lunar EVA."""

    def __init__(self, thresholds: BiometricThresholds = None):
        """Initialize astronaut monitor."""
        self.thresholds = thresholds or BiometricThresholds()
        self.health_log: List[Dict] = []
        self.alert_history: List[Dict] = []

    def assess_health_status(self, biometrics: AstronautBiometrics) -> Tuple[HealthStatus, List[str]]:
        """Assess overall health status and return alerts."""
        alerts = []
        status = HealthStatus.NOMINAL

        # Heart rate assessment
        if biometrics.heart_rate > self.thresholds.heart_rate_critical:
            alerts.append(f"CRITICAL: Heart rate {biometrics.heart_rate} bpm (>150)")
            status = HealthStatus.CRITICAL
        elif biometrics.heart_rate > self.thresholds.heart_rate_max:
            alerts.append(f"WARNING: Elevated heart rate {biometrics.heart_rate} bpm")
            if status != HealthStatus.CRITICAL:
                status = HealthStatus.WARNING

        # Oxygen saturation
        if biometrics.oxygen_saturation < self.thresholds.oxygen_sat_critical:
            alerts.append(f"CRITICAL: Oxygen saturation {biometrics.oxygen_saturation}% (<85%)")
            status = HealthStatus.CRITICAL
        elif biometrics.oxygen_saturation < self.thresholds.oxygen_sat_min:
            alerts.append(f"WARNING: Low oxygen saturation {biometrics.oxygen_saturation}% (<90%)")
            if status != HealthStatus.CRITICAL:
                status = HealthStatus.WARNING

        # Core temperature
        if biometrics.core_temperature > self.thresholds.temp_critical:
            alerts.append(f"CRITICAL: Core temp {biometrics.core_temperature}°C (>39.5°C)")
            status = HealthStatus.CRITICAL
        elif biometrics.core_temperature > self.thresholds.temp_max:
            alerts.append(f"WARNING: High core temp {biometrics.core_temperature}°C")
            if status != HealthStatus.CRITICAL:
                status = HealthStatus.WARNING

        # Blood pressure
        if (biometrics.blood_pressure_sys > self.thresholds.systolic_max or
            biometrics.blood_pressure_dia > self.thresholds.diastolic_max):
            alerts.append(f"WARNING: Elevated blood pressure {biometrics.blood_pressure_sys}/{biometrics.blood_pressure_dia}")
            if status == HealthStatus.NOMINAL:
                status = HealthStatus.CAUTION

        # Fatigue assessment
        if biometrics.fatigue_level > 0.85:
            alerts.append(f"WARNING: High fatigue level {biometrics.fatigue_level:.1%}")
            if status != HealthStatus.CRITICAL:
                status = HealthStatus.WARNING

        return status, alerts

    def assess_suit_status(self, biometrics: AstronautBiometrics) -> Tuple[SuitStatus, List[str]]:
        """Assess suit integrity and environmental conditions."""
        alerts = []
        status = SuitStatus.OPTIMAL

        # Suit pressure
        if biometrics.suit_pressure < self.thresholds.suit_pressure_critical:
            alerts.append(f"CRITICAL: Suit pressure {biometrics.suit_pressure:.1f} PSI (<3.0)")
            status = SuitStatus.EMERGENCY
        elif biometrics.suit_pressure < self.thresholds.suit_pressure_min:
            alerts.append(f"WARNING: Low suit pressure {biometrics.suit_pressure:.1f} PSI (<3.8)")
            status = SuitStatus.COMPROMISED

        # Suit integrity
        if biometrics.suit_integrity < 80:
            alerts.append(f"CRITICAL: Suit integrity compromised {biometrics.suit_integrity:.0f}%")
            status = SuitStatus.EMERGENCY
        elif biometrics.suit_integrity < 95:
            alerts.append(f"WARNING: Suit integrity degraded {biometrics.suit_integrity:.0f}%")
            if status != SuitStatus.EMERGENCY:
                status = SuitStatus.DEGRADED

        # CO2 levels
        if biometrics.co2_level > self.thresholds.co2_critical:
            alerts.append(f"CRITICAL: CO2 level {biometrics.co2_level:.1f}% (>6.0%)")
            status = SuitStatus.EMERGENCY
        elif biometrics.co2_level > self.thresholds.co2_max:
            alerts.append(f"WARNING: Elevated CO2 {biometrics.co2_level:.1f}% (>4.0%)")
            if status != SuitStatus.EMERGENCY:
                status = SuitStatus.COMPROMISED

        # Oxygen remaining
        if biometrics.oxygen_remaining < 0.5:
            alerts.append(f"CRITICAL: Low oxygen reserve {biometrics.oxygen_remaining:.1f} hrs (<0.5)")
            status = SuitStatus.EMERGENCY
        elif biometrics.oxygen_remaining < 1.0:
            alerts.append(f"WARNING: Oxygen reserve {biometrics.oxygen_remaining:.1f} hrs (<1.0)")
            if status != SuitStatus.EMERGENCY:
                status = SuitStatus.COMPROMISED

        # Dust/abrasive contamination
        if biometrics.ambient_dust > self.thresholds.dust_critical:
            alerts.append(f"CRITICAL: Dust contamination {biometrics.ambient_dust:.1f} µg/L (>10.0)")
            status = SuitStatus.EMERGENCY
        elif biometrics.ambient_dust > self.thresholds.dust_max:
            alerts.append(f"WARNING: High dust levels {biometrics.ambient_dust:.1f} µg/L (>5.0)")
            if status != SuitStatus.EMERGENCY:
                status = SuitStatus.DEGRADED

        return status, alerts

    def predict_heart_rate_from_conditions(
        self,
        baseline_heart_rate: int,
        conditions: Dict[str, float],
    ) -> Dict[str, any]:
        """Predict heart rate from the current space environment."""
        radiation = float(conditions.get("radiation_usv_h", conditions.get("radiation", 0.0)))
        temperature = float(conditions.get("temperature_c", conditions.get("temp_c", 0.0)))
        suit_pressure = float(conditions.get("suit_pressure", self.thresholds.suit_pressure_nominal))
        oxygen_saturation = float(conditions.get("oxygen_saturation", 98))
        co2_level = float(conditions.get("co2_level", 2.8))
        dust_level = float(conditions.get("dust_level", conditions.get("pm25_ug_m3", 0.0)))
        metabolic_rate = float(conditions.get("metabolic_rate", 300.0))
        fatigue_level = float(conditions.get("fatigue_level", 0.0))
        work_duration = float(conditions.get("work_duration", 0.0))

        load_bpm = 0.0
        drivers = []

        radiation_load = max(0.0, radiation - 80.0) * 0.12
        if radiation_load > 0:
            drivers.append({"factor": "radiation", "impact_bpm": round(radiation_load, 1)})
        load_bpm += radiation_load

        thermal_load = max(0.0, abs(temperature - 22.0) - 5.0) * 0.08
        if thermal_load > 0:
            drivers.append({"factor": "thermal_stress", "impact_bpm": round(thermal_load, 1)})
        load_bpm += thermal_load

        pressure_load = max(0.0, self.thresholds.suit_pressure_nominal - suit_pressure) * 14.0
        if pressure_load > 0:
            drivers.append({"factor": "suit_pressure", "impact_bpm": round(pressure_load, 1)})
        load_bpm += pressure_load

        oxygen_load = max(0.0, self.thresholds.oxygen_sat_min - oxygen_saturation) * 1.1
        if oxygen_load > 0:
            drivers.append({"factor": "oxygen", "impact_bpm": round(oxygen_load, 1)})
        load_bpm += oxygen_load

        co2_load = max(0.0, co2_level - self.thresholds.co2_max) * 6.5
        if co2_load > 0:
            drivers.append({"factor": "co2", "impact_bpm": round(co2_load, 1)})
        load_bpm += co2_load

        dust_load = max(0.0, dust_level - self.thresholds.dust_max) * 0.35
        if dust_load > 0:
            drivers.append({"factor": "dust", "impact_bpm": round(dust_load, 1)})
        load_bpm += dust_load

        metabolic_load = max(0.0, metabolic_rate - 300.0) / 18.0
        if metabolic_load > 0:
            drivers.append({"factor": "metabolic_rate", "impact_bpm": round(metabolic_load, 1)})
        load_bpm += metabolic_load

        fatigue_load = fatigue_level * 18.0
        if fatigue_load > 0:
            drivers.append({"factor": "fatigue", "impact_bpm": round(fatigue_load, 1)})
        load_bpm += fatigue_load

        duration_load = work_duration * 1.0
        if duration_load > 0:
            drivers.append({"factor": "work_duration", "impact_bpm": round(duration_load, 1)})
        load_bpm += duration_load

        predicted_heart_rate = max(40, int(round(baseline_heart_rate + load_bpm)))

        if predicted_heart_rate >= self.thresholds.heart_rate_critical:
            status = HealthStatus.CRITICAL
        elif predicted_heart_rate > self.thresholds.heart_rate_max:
            status = HealthStatus.WARNING
        elif predicted_heart_rate > self.thresholds.heart_rate_min + 15:
            status = HealthStatus.CAUTION
        else:
            status = HealthStatus.NOMINAL

        warning_signs = []
        if predicted_heart_rate > self.thresholds.heart_rate_max:
            warning_signs.append("Heart rate above the normal EVA range")
        if predicted_heart_rate >= self.thresholds.heart_rate_critical:
            warning_signs.append("Heart rate in the critical zone")
        if radiation >= 90:
            warning_signs.append("High radiation can drive stress and rapid pulse")
        if suit_pressure < self.thresholds.suit_pressure_min:
            warning_signs.append("Low suit pressure can elevate cardiovascular load")
        if oxygen_saturation < self.thresholds.oxygen_sat_min:
            warning_signs.append("Reduced oxygen saturation can trigger tachycardia")
        if co2_level > self.thresholds.co2_max:
            warning_signs.append("Elevated CO2 can cause faster breathing and pulse")
        if fatigue_level > 0.75:
            warning_signs.append("Fatigue is high enough to affect heart rate stability")

        if status == HealthStatus.CRITICAL:
            recommendation = "Stop activity and return to shelter immediately."
        elif status == HealthStatus.WARNING:
            recommendation = "Reduce workload, hydrate, and monitor closely."
        elif status == HealthStatus.CAUTION:
            recommendation = "Schedule a rest break and keep watching the trend."
        else:
            recommendation = "Continue with routine monitoring."

        return {
            "baseline_heart_rate": baseline_heart_rate,
            "predicted_heart_rate": predicted_heart_rate,
            "delta_bpm": predicted_heart_rate - baseline_heart_rate,
            "heart_rate_status": status.value,
            "warning_signs": warning_signs,
            "drivers": drivers,
            "recommendation": recommendation,
        }

    def recommend_action(self, health_status: HealthStatus, suit_status: SuitStatus,
                        biometrics: AstronautBiometrics) -> Dict[str, any]:
        """Recommend actions based on health and suit status."""
        recommendation = {
            "action": "continue",
            "reason": "",
            "urgency": "low",
            "estimated_time_to_base": 0,
        }

        # Critical conditions mandate immediate return
        if health_status == HealthStatus.CRITICAL or suit_status == SuitStatus.EMERGENCY:
            recommendation["action"] = "return_to_base_immediately"
            recommendation["urgency"] = "critical"
            recommendation["reason"] = "Critical health or suit status detected"
            recommendation["estimated_time_to_base"] = self._estimate_return_time(biometrics)
            return recommendation

        # Warning conditions suggest return within safe margin
        if health_status == HealthStatus.WARNING or suit_status == SuitStatus.COMPROMISED:
            recommendation["action"] = "return_to_base"
            recommendation["urgency"] = "high"
            recommendation["reason"] = "Multiple warning conditions detected"
            recommendation["estimated_time_to_base"] = self._estimate_return_time(biometrics)
            return recommendation

        # Caution conditions suggest monitoring and possible early return
        if health_status == HealthStatus.CAUTION or suit_status == SuitStatus.DEGRADED:
            recommendation["action"] = "monitor_closely"
            recommendation["urgency"] = "medium"
            recommendation["reason"] = "Minor concerns detected - monitor biometrics"
            recommendation["estimated_time_to_base"] = self._estimate_return_time(biometrics) * 1.5
            return recommendation

        # Nominal - continue mission
        recommendation["action"] = "continue_mission"
        recommendation["urgency"] = "low"
        recommendation["reason"] = "All systems nominal"
        recommendation["estimated_time_to_base"] = self._estimate_return_time(biometrics)

        return recommendation

    @staticmethod
    def _estimate_return_time(biometrics: AstronautBiometrics) -> float:
        """Estimate time needed to return to base (hours)."""
        # Conservative estimate: 2 hours base time + 30 min safety margin
        # Adjusted by metabolic rate and fatigue
        base_time = 2.5
        fatigue_factor = 1.0 + (biometrics.fatigue_level * 0.5)
        metabolic_factor = biometrics.metabolic_rate / 300.0  # Normalize to 300 kcal/hr baseline
        return base_time * fatigue_factor * metabolic_factor

    def log_biometrics(self, biometrics: AstronautBiometrics):
        """Log biometric data for analysis."""
        self.health_log.append({
            "timestamp": biometrics.timestamp,
            "astronaut_id": biometrics.astronaut_id,
            "heart_rate": biometrics.heart_rate,
            "oxygen_sat": biometrics.oxygen_saturation,
            "core_temp": biometrics.core_temperature,
            "fatigue": biometrics.fatigue_level,
        })

    def log_alert(self, alert: Dict):
        """Log safety alert."""
        self.alert_history.append(alert)


class SuitEnvironmentMonitor:
    """Monitor suit environmental conditions."""

    @staticmethod
    def assess_dust_impact(dust_level: float, work_duration: float) -> Dict:
        """Assess impact of dust on suit systems over time."""
        # Dust degradation model (exponential)
        degradation_rate = 0.02 * dust_level  # % per hour
        cumulative_degradation = degradation_rate * work_duration

        return {
            "dust_level": dust_level,
            "work_duration": work_duration,
            "degradation_rate": degradation_rate,
            "cumulative_degradation": cumulative_degradation,
            "suit_integrity_remaining": max(0, 100 - cumulative_degradation),
            "recommendation": (
                "RETURN TO BASE NOW" if dust_level > 10.0 else
                "Increase cleaning frequency" if dust_level > 5.0 else
                "Normal operations"
            ),
        }

    @staticmethod
    def predict_oxygen_depletion(
        oxygen_remaining: float,
        metabolic_rate: float,
        work_efficiency: float = 1.0
    ) -> Dict:
        """Predict time to oxygen depletion."""
        consumption_rate = metabolic_rate / 3000.0  # Convert kcal/hr to suit oxygen %/hr
        hours_remaining = oxygen_remaining / (consumption_rate * work_efficiency)

        return {
            "oxygen_remaining": oxygen_remaining,
            "consumption_rate": consumption_rate,
            "work_efficiency": work_efficiency,
            "hours_remaining": hours_remaining,
            "safe_margin_hours": 1.0,  # Always maintain 1-hour emergency reserve
            "immediate_action_threshold": 2.0,  # Return if <2 hours remaining
            "should_return": hours_remaining < 2.0,
        }


class CrewHealthTeam:
    """Manage health monitoring for entire crew."""

    def __init__(self):
        """Initialize crew health team."""
        self.astronauts: Dict[str, AstronautMonitor] = {}
        self.mission_start_time: float = 0
        self.base_location: Tuple[float, float] = (0, 0)

    def register_astronaut(self, astronaut_id: str):
        """Register astronaut for monitoring."""
        self.astronauts[astronaut_id] = AstronautMonitor()

    def update_biometrics(self, biometrics: AstronautBiometrics) -> Dict:
        """Update and assess astronaut biometrics."""
        if biometrics.astronaut_id not in self.astronauts:
            self.register_astronaut(biometrics.astronaut_id)

        monitor = self.astronauts[biometrics.astronaut_id]
        monitor.log_biometrics(biometrics)

        health_status, health_alerts = monitor.assess_health_status(biometrics)
        suit_status, suit_alerts = monitor.assess_suit_status(biometrics)
        recommendation = monitor.recommend_action(health_status, suit_status, biometrics)

        all_alerts = health_alerts + suit_alerts

        if all_alerts:
            alert = {
                "timestamp": biometrics.timestamp,
                "astronaut_id": biometrics.astronaut_id,
                "health_status": health_status.value,
                "suit_status": suit_status.value,
                "alerts": all_alerts,
                "recommendation": recommendation["action"],
            }
            monitor.log_alert(alert)

        return {
            "astronaut_id": biometrics.astronaut_id,
            "health_status": health_status.value,
            "suit_status": suit_status.value,
            "alerts": all_alerts,
            "recommendation": recommendation,
        }

    def get_mission_summary(self) -> Dict:
        """Get summary of crew health status."""
        return {
            "crew_size": len(self.astronauts),
            "monitors": {
                astronaut_id: {
                    "biometric_logs": len(monitor.health_log),
                    "total_alerts": len(monitor.alert_history),
                }
                for astronaut_id, monitor in self.astronauts.items()
            },
        }


# Example usage
if __name__ == "__main__":
    print("=== Astronaut Health Monitoring System ===\n")

    # Create monitor
    monitor = AstronautMonitor()

    # Simulate astronaut data
    biometrics = AstronautBiometrics(
        astronaut_id="EVA-001",
        timestamp=1000.0,
        heart_rate=105,
        blood_pressure_sys=135,
        blood_pressure_dia=85,
        core_temperature=37.8,
        oxygen_saturation=96,
        respiration_rate=18,
        suit_pressure=4.2,
        oxygen_remaining=3.5,
        co2_level=3.2,
        suit_integrity=98.5,
        ambient_dust=2.1,
        suit_temperature=18.5,
        radiation_exposure=0.15,
        metabolic_rate=350,
        work_duration=1.5,
        fatigue_level=0.45,
    )

    # Assess health
    health_status, health_alerts = monitor.assess_health_status(biometrics)
    suit_status, suit_alerts = monitor.assess_suit_status(biometrics)
    recommendation = monitor.recommend_action(health_status, suit_status, biometrics)

    print(f"Astronaut ID: {biometrics.astronaut_id}")
    print(f"Health Status: {health_status.value}")
    print(f"Suit Status: {suit_status.value}\n")

    print("Health Alerts:")
    for alert in health_alerts:
        print(f"  - {alert}")

    print("\nSuit Alerts:")
    for alert in suit_alerts:
        print(f"  - {alert}")

    print(f"\nRecommendation: {recommendation['action']}")
    print(f"  Reason: {recommendation['reason']}")
    print(f"  Urgency: {recommendation['urgency']}")
    print(f"  Est. return time: {recommendation['estimated_time_to_base']:.1f} hrs")

    # Test dust impact
    print("\n=== Dust Impact Analysis ===")
    dust_impact = SuitEnvironmentMonitor.assess_dust_impact(
        dust_level=3.5,
        work_duration=2.0
    )
    print(f"Dust Level: {dust_impact['dust_level']:.1f} µg/L")
    print(f"Work Duration: {dust_impact['work_duration']:.1f} hrs")
    print(f"Suit Integrity Remaining: {dust_impact['suit_integrity_remaining']:.1f}%")
    print(f"Recommendation: {dust_impact['recommendation']}")

    # Test oxygen prediction
    print("\n=== Oxygen Depletion Prediction ===")
    oxygen_pred = SuitEnvironmentMonitor.predict_oxygen_depletion(
        oxygen_remaining=3.5,
        metabolic_rate=350,
        work_efficiency=0.95
    )
    print(f"Hours Remaining: {oxygen_pred['hours_remaining']:.1f} hrs")
    print(f"Safe Margin: {oxygen_pred['safe_margin_hours']:.1f} hrs")
    print(f"Should Return: {oxygen_pred['should_return']}")
