# Autonomous Rover AI System

An autonomous rover system that combines multimodal sensor fusion, computer vision, LLM reasoning, and robotic control to explore unknown terrain and produce scientific reports.

## Overview

This system demonstrates the complete autonomous science pipeline:

```
Sense → Reason → Decide → Move → Explain
```

The rover:
- 🛰️ Explores unknown lunar terrain in simulation
- 🪨 Detects and classifies rocks using computer vision
- 🔬 Fuses camera, depth, and spectral data to infer composition
- 🧠 Uses an LLM to explain scientific significance
- 🚗 Plans safe routes while avoiding hazards
- 📡 Operates autonomously despite communication constraints
- 📝 Produces scientific reports ranking sample locations

## Features

- **Multimodal Sensor Fusion**: Combines vision, depth, thermal, and spectral sensors
- **Computer Vision**: Rock detection, classification, and segmentation
- **LLM Reasoning**: Claude/GPT integration for scientific explanation
- **Motion Planning**: Autonomous navigation with obstacle avoidance
- **MuJoCo Simulation**: Realistic lunar terrain and rover physics
- **Science Report Generation**: Automated sample ranking and analysis

## Project Structure

```
AI-Lab-Robot/
├── main.py                  # Rover mission entry point
├── rover/
│   ├── __init__.py
│   ├── rover.py            # Rover controller
│   ├── navigation.py       # Path planning and autonomy
│   └── gripper.py          # Sample collection mechanism
├── sensors/
│   ├── __init__.py
│   ├── camera.py           # RGB vision
│   ├── depth.py            # Depth sensor
│   ├── thermal.py          # Thermal imaging
│   └── spectral.py         # Simulated spectral analysis
├── ai/
│   ├── __init__.py
│   ├── vision/
│   │   ├── rock_detector.py      # YOLO/DETR rock detection
│   │   ├── classifier.py         # Rock classification
│   │   └── segmentation.py       # Semantic segmentation
│   ├── fusion/
│   │   └── sensor_fusion.py      # Multimodal data fusion
│   ├── reasoning/
│   │   ├── scientist.py          # LLM-based reasoning
│   │   └── explainer.py          # Report generation
│   └── planning/
│       ├── route_planner.py      # A*, RRT path planning
│       └── task_planner.py       # High-level mission planning
├── simulation/
│   ├── __init__.py
│   ├── environment.py       # MuJoCo lunar terrain
│   ├── renderer.py          # Visualization
│   └── scenarios/
│       ├── terrain_1.xml
│       ├── terrain_2.xml
│       └── terrain_hazard.xml
├── datasets/
│   ├── lunar_rocks/         # Training data for rock classification
│   └── terrain_samples/     # Lunar terrain datasets
├── evaluation/
│   ├── benchmarks.py        # Performance metrics
│   └── reports/             # Generated science reports
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Installation

### Prerequisites
- Python 3.9+
- MuJoCo 3.x
- CUDA (optional, for faster inference)

### Setup

```bash
cd LunaMind
pip install -r requirements.txt
```

## Dependencies

Core packages:
- **mujoco**: Physics simulation and lunar terrain
- **torch**: Deep learning for vision
- **transformers**: LLM integration (Claude, GPT)
- **opencv-python**: Computer vision processing
- **numpy/scipy**: Numerical computing
- **anthropic**: Claude API for scientific reasoning

## Usage

### Basic Mission

```bash
# Run a simple exploration mission
python main.py --mission explore --terrain simple

# Run hazard avoidance mission
python main.py --mission explore --terrain hazard --avoid-obstacles

# Run with LLM reasoning
python main.py --mission explore --use-llm --model claude-opus

# Generate science report
python main.py --mission explore --generate-report
```

### Available Missions
- `explore`: Autonomous terrain exploration
- `sample_collection`: Identify and collect valuable samples
- `hazard_assessment`: Detect and avoid hazards
- `scientific_survey`: Full survey with reporting

### Available Terrains
- `simple`: Flat terrain with isolated rocks
- `complex`: Varied topography with obstacles
- `hazard`: Dangerous terrain with radiation/thermal hazards
- `realistic`: Simulated lunar regolith

## Architecture

### Sensor Pipeline

```
Camera → Rock Detector → Classifier
Depth   → Segmentation → Spatial Map
Thermal → Anomaly Detection → Hazard Map
Spectral → Composition Inference → Element Map
           ↓
        Sensor Fusion → World Model
           ↓
        LLM Reasoning → Scientific Assessment
           ↓
        Motion Planner → Navigation Commands
           ↓
        Rover Control → Physical Movement
```

### Key Components

1. **Rover (rover/rover.py)**
   - State management
   - Sensor integration
   - Motor control

2. **Vision System (ai/vision/)**
   - Rock detection using YOLO/DETR
   - Rock classification (basalt, granite, olivine, etc.)
   - Anomaly detection

3. **Sensor Fusion (ai/fusion/sensor_fusion.py)**
   - Combines multiple sensor modalities
   - Maintains consistent world model
   - Handles uncertainty

4. **LLM Scientist (ai/reasoning/scientist.py)**
   - Analyzes fused sensor data
   - Reasons about scientific significance
   - Explains findings in natural language

5. **Motion Planner (ai/planning/route_planner.py)**
   - A* path planning
   - RRT for complex terrain
   - Obstacle avoidance

6. **Simulation (simulation/environment.py)**
   - MuJoCo-based lunar terrain
   - Realistic physics
   - Sensor simulation

## Research Questions

1. **Can multimodal sensor fusion improve scientific sample selection?**
2. **Can LLMs reason effectively over fused sensor data in resource-constrained environments?**
3. **How does autonomous terrain exploration compare with human-guided remote operation?**
4. **Can AI identify scientifically valuable samples without human input?**
5. **How does communication delay affect autonomous decision-making?**

## Example Output

```
LunaMind Science Report
======================

Mission: Explore Terrain A
Duration: 45 minutes
Samples Analyzed: 23

Top 5 Scientifically Valuable Samples:
1. Sample #8 (Olivine basalt) - Age indicator, composition suggests subsurface activity
2. Sample #14 (Anorthosite) - Early lunar crust, pristine preservation
3. Sample #3 (Regolith with Fe-oxide) - Evidence of water alteration
4. Sample #19 (Impact breccia) - Timeline of major impact events
5. Sample #11 (Layered deposit) - Stratigraphic sequence

Hazards Detected: 2
- Elevated radiation zone near crater rim
- Unstable terrain slope at 35° (impassable)

Recommendations:
- Prioritize Sample #8 for collection (accessible, high scientific value)
- Avoid crater rim (radiation levels 2.3x background)
- Explore northern plateau for additional samples
```

## Integration with Real Hardware

The modular design allows easy transition to real hardware:

1. Replace MuJoCo simulation with real rover telemetry
2. Connect real camera/depth streams to vision modules
3. Integrate actual rover control API
4. Add real spectral analyzer output
5. Maintain same LLM reasoning pipeline

## Dataset Resources

- [Hugging Face Robotics Datasets](https://huggingface.co/datasets?task_categories=task_categories:robotics)
- [Kaggle Robotics Datasets](https://www.kaggle.com/datasets)
- [MuJoCo Documentation](https://www.mujoco.org/)


## Future Enhancements

- [ ] Real rover hardware integration (e.g., JPL RoboSimian)
- [ ] Reinforcement learning for navigation policies
- [ ] Multi-rover coordination and communication
- [ ] Fine-tuning LLMs on lunar science literature
- [ ] Sim-to-real transfer learning
- [ ] Long-term autonomy (power, battery management)
- [ ] Sample caching and retrieval strategies

## Contributing

Contributions welcome! Key areas:
- Vision model improvements
- Sensor fusion algorithms
- LLM prompt engineering
- Path planning optimization
- Simulation realism

## References

- Lim et al. (2021) - Autonomous lunar exploration
- Thrun et al. - Probabilistic robotics
- Dosovitskiy et al. (2015) - FlowNet for depth estimation
- CLIP & Vision Transformers - Multimodal reasoning
