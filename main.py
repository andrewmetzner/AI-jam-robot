#!/usr/bin/env python3
"""
AI Lab Robot - Main entry point
Robotic arm control with LLM planning and computer vision
"""

import argparse
from simulation import MuJoCoSimulator
from planner import LLMPlanner
from controller import RobotController
from vision import VisionSystem


def main():
    parser = argparse.ArgumentParser(description="AI Lab Robot Controller")
    parser.add_argument("--scene", default="scenes/lab_scene.xml", help="MuJoCo scene file")
    parser.add_argument("--headless", action="store_true", help="Run without visualization")
    parser.add_argument("--task", default="pick_and_place", help="Task to execute")
    args = parser.parse_args()

    # Initialize components
    simulator = MuJoCoSimulator(scene_path=args.scene, headless=args.headless)
    planner = LLMPlanner()
    controller = RobotController(simulator)
    vision = VisionSystem()

    # Execute task
    print(f"Executing task: {args.task}")
    plan = planner.generate_plan(args.task)
    controller.execute_plan(plan)

    simulator.close()


if __name__ == "__main__":
    main()
