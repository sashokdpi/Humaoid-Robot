#!/usr/bin/env bash
# Source on Jetson before Physical AI pipeline
export PHYSICAL_AI_ROBOT=xarm6
export PHYSICAL_AI_ARM_VARIANT=xarm6
export PHYSICAL_AI_GRIPPER=1
export PHYSICAL_AI_GRIPPER_TYPE=ufactory_standard
export PHYSICAL_AI_ADD_GRIPPER=true
# xarm_ros2: use add_gripper only (do NOT set add_bio_gripper or add_vacuum_gripper)
export PHYSICAL_AI_JOINT_NAMES=joint1,joint2,joint3,joint4,joint5,joint6
export PHYSICAL_AI_TRAJECTORY_ACTION=/xarm6_traj_controller/follow_joint_trajectory
export PHYSICAL_AI_MOVE_GROUP=xarm6
export PHYSICAL_AI_PLANNING_FRAME=link_base
export PHYSICAL_AI_EE_LINK=link_eef
export PHYSICAL_AI_GRIPPER_ACTION=/xarm_gripper/gripper_action
export PHYSICAL_AI_JOINT_STATES_TOPIC=/joint_states
# Set your controller IP:
export XARM_IP="${XARM_IP:-192.168.1.206}"
export PHYSICAL_AI_XARM_IP="${XARM_IP}"
echo "Physical AI: xArm6 + gripper | XARM_IP=${XARM_IP}"
