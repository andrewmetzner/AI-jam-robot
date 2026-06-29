# AI Lab Robot

A robotic control system combining LLM planning, computer vision, and MuJoCo simulation.

## Features

- **MuJoCo Simulation**: Physics-based simulation environment for robot learning and testing
- **LLM Planning**: Natural language task planning using large language models
- **Robot Control**: Real-time control of robotic arm with inverse kinematics
- **Vision System**: Object detection and pose estimation (placeholder for integration)
- **Dataset Integration**: Support for robotics datasets from Hugging Face and Kaggle

## Project Structure

```
AI-Lab-Robot/
├── main.py              # Entry point
├── planner.py           # LLM task planning
├── controller.py        # Robot action execution
├── vision.py            # Object detection & pose estimation
├── simulation.py        # MuJoCo interface
├── models/              # Pre-trained model weights
├── scenes/              # MuJoCo XML scene files
│   └── lab_scene.xml    # Lab environment with robotic arm
├── datasets/            # Downloaded robotics datasets
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Installation

### Prerequisites
- Python 3.8+
- MuJoCo (free license available)

### Setup

```bash
# Clone or create the project
cd AI-Lab-Robot

# Install dependencies
pip install -r requirements.txt
```

## Dependencies

Core packages:
- **mujoco**: Physics simulation
- **opencv-python**: Computer vision
- **torch**: Deep learning framework
- **transformers**: LLM integration
- **numpy**: Numerical computing
- **Pillow**: Image processing

## Usage

### Basic Usage

```bash
# Run with default scene and pick-and-place task
python main.py

# Run specific task
python main.py --task grasp

# Run without visualization
python main.py --headless

# Use custom scene
python main.py --scene scenes/lab_scene.xml --task move
```

### Available Tasks
- `pick_and_place`: Pick object and place in target location
- `grasp`: Grasp object with gripper
- `move`: Move to target position

## Architecture

### Components

1. **Simulation (simulation.py)**
   - Loads MuJoCo XML scenes
   - Steps physics simulation
   - Retrieves body positions and states

2. **Planner (planner.py)**
   - Generates action sequences from task descriptions
   - Integrates with LLM APIs (Claude, GPT, etc.)
   - Returns waypoints and actions

3. **Controller (controller.py)**
   - Executes planned actions
   - Implements inverse kinematics
   - Manages gripper/grasping

4. **Vision (vision.py)**
   - Object detection (YOLO, DETR)
   - 6D pose estimation
   - Semantic segmentation

## Dataset Resources

- [Hugging Face Robotics Datasets](https://huggingface.co/datasets?task_categories=task_categories:robotics)
- [Kaggle Robotics Datasets](https://www.kaggle.com/datasets)
- [MuJoCo Documentation](https://www.mujoco.org/)

## Development

### Adding New Tasks

Edit `planner.py` to add new task prompts:

```python
self.task_prompts["new_task"] = "Task description for LLM"
```

### Integrating LLM APIs

Update `planner.py` to connect to your LLM:

```python
def generate_plan(self, task: str) -> list:
    # Call LLM API to generate plan
    response = llm_client.complete(prompt)
    return parse_actions(response)
```

### Custom MuJoCo Scenes

Create new XML files in `scenes/` directory following MuJoCo XML format.

## Future Enhancements

