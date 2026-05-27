#!/usr/bin/env bash
# xArm6 + UFACTORY gripper — ROS2 Humble (Jetson / Ubuntu 22.04)
# Usage: export XARM_IP=192.168.1.XXX && bash scripts/xarm6_ros2_start.sh [fake|real]

set -euo pipefail
MODE="${1:-real}"
ROBOT_IP="${XARM_IP:-192.168.1.206}"
# Standard UFACTORY parallel gripper only (not bio / vacuum)
ADD_GRIPPER="${PHYSICAL_AI_ADD_GRIPPER:-true}"

source /opt/ros/humble/setup.bash

if [ -f "${XARM_WS:-$HOME/xarm_ws}/install/setup.bash" ]; then
  source "${XARM_WS:-$HOME/xarm_ws}/install/setup.bash"
elif [ -f ~/dev_ws/install/setup.bash ]; then
  source ~/dev_ws/install/setup.bash
else
  echo "Build xarm_ros2 first: https://github.com/xArm-Developer/xarm_ros2 (branch humble)"
  exit 1
fi

echo "xArm6 @ ${ROBOT_IP} | gripper=${ADD_GRIPPER} | mode=${MODE}"

if [ "$MODE" = "fake" ]; then
  # No hardware — RViz + ros2_control sim
  exec ros2 launch xarm_moveit_config xarm6_moveit_fake.launch.py \
    add_gripper:=${ADD_GRIPPER}
else
  # Real arm + MoveIt + gripper (pinned xarm_ros2 Humble launch)
  exec ros2 launch xarm_moveit_config xarm6_moveit_realmove.launch.py \
    robot_ip:="${ROBOT_IP}" \
    add_gripper:=${ADD_GRIPPER}
fi
