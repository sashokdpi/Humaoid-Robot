#!/usr/bin/env bash
# Build Physical AI ROS2 workspace (Ubuntu 22.04 + ROS2 Humble on Jetson or PC)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WS="$ROOT/robotics/ros2_ws"

source /opt/ros/humble/setup.bash
cd "$WS"
colcon build --symlink-install
echo "source $WS/install/setup.bash"
