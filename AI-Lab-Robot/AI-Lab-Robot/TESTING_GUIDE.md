# Mock Dataset Testing Guide

## Overview

This guide explains how to test the autonomous rover system using pre-built mock datasets and machine learning models.

---

## Quick Start

### 1. List Available Datasets

```bash
cd AI-Lab-Robot
python main.py --list-datasets
```

**Output:**
```
Available Datasets:

  simple       - Flat terrain, isolated rocks, ideal for beginner testing
  complex      - Hilly terrain, navigation hazards, thermal anomalies
  crater       - Crater rim survey with coring opportunities
  hazard       - Radiation hotspot with few accessible samples
  drill        - Locations optimized for coring and subsurface sampling
```

### 2. Run a Mission with a Dataset

```bash
# Run exploration mission with simple dataset
python main.py --dataset simple --mission explore

# Run with complex terrain
python main.py --dataset complex --mission explore --generate-report

# Enable LLM-based reasoning
python main.py --dataset crater --use-llm --mission explore
```

---

## Available Datasets

### 1. **Simple Survey** (`simple`)
- **Terrain:** Flat, low-slope regions
- **Difficulty:** Easy (beginner testing)
- **Locations:** 5
- **Rock Types:** Basalt, Olivine, Anorthosite, Regolith
- **Hazards:** None
- **Best For:** Testing basic navigation and sample collection
- **Command:**
  ```bash
  python main.py --dataset simple --mission explore
  ```

---

### 2. **Complex Terrain** (`complex`)
- **Terrain:** Hilly, slopes up to 25°
- **Difficulty:** Hard
- **Locations:** 6
- **Rock Types:** Mixed compositions with high-value samples
- **Hazards:** Thermal anomalies, radiation zones
- **Terrain Slopes:** 3-12 degrees
- **Best For:** Testing navigation algorithms and hazard avoidance
- **Command:**
  ```bash
  python main.py --dataset complex --mission explore --generate-report
  ```

---

### 3. **Crater Exploration** (`crater`)
- **Terrain:** Crater rim (slopes 15-25°)
- **Difficulty:** Medium-Hard
- **Locations:** 7
- **Subsurface Access:** Coring opportunities at all locations
- **Coring Depths:** 1-3 meters
- **Expected Subsurface:** Olivine-rich, mixed compositions, plagioclase, basaltic flows
- **Best For:** Testing subsurface drilling, core sample analysis
- **Ground Truth Valuable:** Locations 1, 2, 5, 6 (high-value olivine/anorthosite)
- **Command:**
  ```bash
  python main.py --dataset crater --mission explore
  ```

---

### 4. **Hazardous Zone** (`hazard`)
- **Terrain:** Flat to gentle slopes
- **Difficulty:** Hard (risk assessment)
- **Locations:** 4
- **Radiation Levels:** 300-1200 mSv/year (hazardous)
- **Critical Zone:** Location 2 at center (AVOID)
- **Thermal Hazards:** Multiple locations with heat signatures
- **Best For:** Testing hazard detection, risk-aware planning, selective sampling
- **Safe Samples:** Only Location 1 is both safe and valuable
- **Command:**
  ```bash
  python main.py --dataset hazard --mission explore
  ```

---

### 5. **Drill Sites** (`drill`)
- **Terrain:** Optimal for drilling (flat)
- **Difficulty:** Medium
- **Locations:** 5
- **Deep Drilling Targets:** 1-3 meters depth at each location
- **Priority Levels:** Critical, High, Medium
- **Expected Materials:**
  - Basalt lava flows
  - Olivine-rich dunite
  - Mantle material
  - Highland material
  - Subsurface ice signatures
- **Best For:** Testing deep coring, stratified sampling, subsurface science
- **Command:**
  ```bash
  python main.py --dataset drill --mission explore
  ```

---

## Testing Workflows

### Test 1: Basic Functionality

```bash
# Run with minimal features
python main.py --dataset simple --mission explore

# Expected: 5 locations explored, 10+ samples analyzed, report generated
```

### Test 2: Navigation & Hazards

```bash
# Test complex terrain navigation
python main.py --dataset complex --mission explore --generate-report

# Test hazard avoidance
python main.py --dataset hazard --mission explore --generate-report

# Expected: Rovers avoid high-radiation zones, prioritize accessible samples
```

### Test 3: Scientific Depth

```bash
# Test subsurface analysis
python main.py --dataset crater --mission explore --generate-report

# Test drilling prioritization
python main.py --dataset drill --mission explore --generate-report

# Expected: Subsurface composition predictions, coring recommendations
```

### Test 4: LLM Integration

```bash
# Enable Claude-based reasoning
python main.py --dataset simple --use-llm --mission explore

# Expected: Detailed scientific explanations for each sample
```

### Test 5: All Datasets Sequential

```bash
python test_datasets.py all

# Expected: 5 missions run, results summary displayed
```

---

## Machine Learning Models

### 1. Rock Type Classifier (`ai/ml_models.py`)

**Purpose:** Classify rock types using spectral features

**Models:**
- Random Forest (50 estimators)
- Handles: Basalt, Olivine, Anorthosite, Regolith

**Input Features:**
- Fe (Iron concentration)
- Mg (Magnesium concentration)
- Si (Silicon concentration)
- Visual confidence
- Spectral confidence

**Output:** Predicted rock type + confidence score

**Example Usage:**
```python
from ai.ml_models import RockTypeClassifier

classifier = RockTypeClassifier()
features = [0.15, 0.12, 0.25, 0.85, 0.80]  # Fe, Mg, Si, vis_conf, spec_conf
rock_type, confidence = classifier.predict(features)
# Output: ("basalt", 0.92)
```

---

### 2. Sample Value Predictor (`ai/ml_models.py`)

**Purpose:** Predict scientific value of samples

**Model:** Gradient Boosting Regressor (50 estimators)

**Input Features:**
- Visual confidence (0-1)
- Spectral confidence (0-1)
- Rock rarity (0-1, where 1=rare)
- Accessibility (0-1, where 1=easy to reach)
- Depth (meters below surface)

**Output:** Scientific value score (0-1)

**Example Usage:**
```python
from ai.ml_models import SampleValuePredictor

predictor = SampleValuePredictor()
sample = {
    "visual_confidence": 0.90,
    "spectral_confidence": 0.85,
    "rarity": 0.8,
    "accessibility": 0.9,
    "depth": 0.5,
}
value = predictor.predict_value(sample)
# Output: 0.78
```

---

### 3. Sample Clustering (`ai/ml_models.py`)

**Purpose:** Group samples by composition or location

**Algorithms:**
- K-Means clustering (configurable k)
- Supports composition-based or location-based grouping

**Example Usage:**
```python
from ai.ml_models import SampleClustering

# Cluster by composition
clusters = SampleClustering.cluster_by_composition(samples, n_clusters=3)
# Returns: {0: [samples...], 1: [samples...], 2: [samples...]}

# Cluster by location
location_clusters = SampleClustering.cluster_by_location(samples, n_clusters=2)
```

---

### 4. Anomaly Detection (`ai/ml_models.py`)

**Purpose:** Detect unusual samples for special investigation

**Algorithm:** Isolation Forest

**Features Used:**
- Visual confidence
- Spectral confidence
- Overall confidence

**Example Usage:**
```python
from ai.ml_models import AnomalyDetector

anomalies = AnomalyDetector.detect_anomalies(samples, contamination=0.1)
# Returns: [{"sample_id": 5, "reason": "Unusual spectral signature detected", "anomaly_score": 0.95}]
```

---

## Test Script Usage

### Run all datasets

```bash
python test_datasets.py all
```

### Test dataset-specific features

```bash
python test_datasets.py features
```

### Run single dataset

```bash
python test_datasets.py simple
python test_datasets.py complex
python test_datasets.py crater
python test_datasets.py hazard
python test_datasets.py drill
```

### List datasets

```bash
python test_datasets.py list
```

---

## Expected Output Examples

### Simple Dataset Output

```
============================================================
AUTONOMOUS EXPLORATION MISSION INITIATED
============================================================

Loaded dataset: Simple Survey

✓ Sensors active: Camera, Depth, Thermal, Spectral
✓ Fused 2 rock detections
✓ Analyzed 2 samples
✓ Next waypoint: (25, 0)
✓ Rover position: (25, 0)

[... 4 more locations ...]

============================================================
SCIENCE REPORT
============================================================

Mission Summary:
  - Samples Analyzed: 10
  - Battery Remaining: 92.3%
  - Samples Collected: 0

Top 5 Scientifically Valuable Samples:

1. Sample #1 (OLIVINE)
   Scientific Value: 0.89
   Notes: Mantle material; reveals subsurface composition...

2. Sample #2 (ANORTHOSITE)
   Scientific Value: 0.87
   Notes: Ancient lunar highlands; records early lunar...

[... more samples ...]

Recommendations:
  - Prioritize high-value olivine and anorthosite samples
  - Return to base when battery < 10%
  - Next mission: explore southern plateau
```

---

## Debugging & Customization

### Modify Dataset Locations

Edit `data/datasets.py` to add new test scenarios:

```python
@staticmethod
def custom_scenario() -> Dict:
    return {
        "name": "Custom Scenario",
        "description": "Your description here",
        "num_locations": 3,
        "locations": [
            {
                "id": 0,
                "position": (0, 0),
                "rocks": [
                    {"id": 0, "type": "basalt", "confidence": 0.85, "bbox": (150, 200, 80, 70)},
                ],
                "hazards": [],
                "terrain_slope": 0.0,
            },
            # ... more locations
        ],
        "ground_truth_valuable": [0],
    }
```

### Tune ML Models

Modify `ai/ml_models.py` to adjust:
- Number of estimators
- Regularization strength
- Clustering parameters
- Anomaly contamination rate

### Performance Metrics

Track mission success by monitoring:
- Battery consumption
- Sample collection efficiency
- Hazard avoidance success rate
- Scientific value of collected samples

---

## Troubleshooting

### "Unknown dataset" Error

```bash
python main.py --list-datasets
# See available options
```

### LLM Not Working

```bash
# Check ANTHROPIC_API_KEY is set
export ANTHROPIC_API_KEY="your-key"
python main.py --dataset simple --use-llm
```

### ML Models Not Loading

```bash
# Install scikit-learn
pip install scikit-learn>=1.3.0

# Verify installation
python -c "import sklearn; print(sklearn.__version__)"
```

---

## Next Steps

1. ✅ Run simple dataset test
2. ✅ Explore complex terrain handling
3. ✅ Test hazard detection
4. ✅ Integrate LLM reasoning
5. ✅ Evaluate ML model predictions
6. ✅ Customize datasets for your scenarios
7. ✅ Benchmark performance metrics
