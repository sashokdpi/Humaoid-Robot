#!/usr/bin/env bash
# MoveIt2 only (when driver already running) — xArm6 + gripper
set -euo pipefail
ROBOT_IP="${XARM_IP:-192.168.1.206}"
ADD_GRIPPER="${PHYSICAL_AI_ADD_GRIPPER:-true}"
MODE="${1:-fake}"

source /opt/ros/humble/setup.bash
source "${XARM_WS:-$HOME/xarm_ws}/install/setup.bash"

if [ "$MODE" = "real" ]; then
  ros2 launch xarm_moveit_config xarm6_moveit_realmove.launch.py \
    robot_ip:="${ROBOT_IP}" add_gripper:=${ADD_GRIPPER}
else
  ros2 launch xarm_moveit_config xarm6_moveit_fake.launch.py \
    add_gripper:=${ADD_GRIPPER}
fi
