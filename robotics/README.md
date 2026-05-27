# Physical AI — xArm6 + ROS2 Humble

Default robot: **UFACTORY xArm6** (joints `joint1`–`joint6`, MoveIt group `xarm6`).

## xArm6 quick reference

| Item | Value |
|------|--------|
| Joints | `joint1` … `joint6` |
| Gripper | **Standard UFACTORY** parallel (`add_gripper:=true`) |
| Gripper joint | `drive_joint` |
| Trajectory action | `/xarm6_traj_controller/follow_joint_trajectory` |
| Gripper action | `/xarm_gripper/gripper_action` |
| Gripper services | `/xarm/set_gripper_position` (0–850 mm) |
| MoveIt groups | `xarm6`, `xarm_gripper` |
| Planning frame | `link_base` |
| End effector | `link_eef` |
| Default IP | `192.168.1.206` (set `XARM_IP`) |

## Jetson AGX Orin (recommended platform)

AGX has enough RAM/GPU to run **ROS2 + YOLO + ONNX RL + PINN** together.

```bash
# Max performance mode
sudo nvpmodel -m 0
sudo jetson_clocks

# Use AGX env template
cp config/jetson_agx.env.example config/jetson.env
# Edit XARM_IP, then:
source config/jetson.env
```

| AGX Orin | AGX Xavier (older) |
|----------|-------------------|
| JetPack 6, Ubuntu 22.04, Humble | JetPack 5.1, Ubuntu 20.04 → use ROS Foxy or upgrade to 22.04 |
| `pip` PyTorch from NVIDIA JP6 wheel | JP5.1 PyTorch wheel (different URL) |

## 1. Install xarm_ros2 (Jetson / Ubuntu 22.04)

```bash
sudo apt install ros-humble-moveit ros-humble-ros2-control ros-humble-xacro
mkdir -p ~/xarm_ws/src && cd ~/xarm_ws/src
git clone https://github.com/xArm-Developer/xarm_ros2.git -b humble
cd ~/xarm_ws && colcon build
source ~/xarm_ws/install/setup.bash
```

Set arm IP (default factory IP often `192.168.1.206`):

```bash
export XARM_IP=192.168.1.XXX
```

## 2. Build Physical AI workspace

```bash
cd physical_ai_system
pip install -r requirements-physical-ai.txt
bash scripts/build_ros2_ws.sh
source robotics/ros2_ws/install/setup.bash
export PHYSICAL_AI_ROOT=$(pwd)
source scripts/xarm6_env.sh
```

## 3. Launch stack (Jetson)

**Terminal A — xArm6 driver + MoveIt + gripper** (pinned Humble launches):

```bash
cp config/jetson.env.example config/jetson.env   # edit XARM_IP
source config/jetson.env
source ~/xarm_ws/install/setup.bash
bash scripts/xarm6_ros2_start.sh real
# Simulation without arm: bash scripts/xarm6_ros2_start.sh fake
```

**Terminal B — (optional) MoveIt only** if driver already running:

```bash
bash scripts/xarm6_moveit.sh real   # or: fake
```

**Terminal C — Perception (RealSense + YOLO on GPU)**:

```bash
source robotics/ros2_ws/install/setup.bash
ros2 launch physical_ai_bringup xarm6_bringup.launch.py yolo_device:=cuda:0
```

**Terminal D — Physical AI pipeline**:

```bash
source scripts/xarm6_env.sh
export PHYSICAL_AI_MODE=hardware
export PHYSICAL_AI_PERCEPTION=ros2
export PHYSICAL_AI_ROBOT_BACKEND=ros2
python run.py "Pick the red bottle"
```

## 4. Modes

| Mode | Command |
|------|---------|
| Sim (Windows/PC) | `python run.py "Pick the red bottle"` |
| Hybrid (camera only) | `PHYSICAL_AI_MODE=hybrid python run.py "..."` |
| Full hardware | `source scripts/xarm6_env.sh` + `PHYSICAL_AI_MODE=hardware` |

## 5. RViz — xArm6 model

```bash
ros2 launch physical_ai_description xarm6_display.launch.py
# With official meshes from xarm_ros2:
ros2 launch physical_ai_description xarm6_display.launch.py use_official_urdf:=true
```

## 6. Gripper — standard UFACTORY

This project is configured for the **factory xArm parallel gripper**, not BIO or vacuum.

xarm_ros2 launches must use `add_gripper:=true` only (never `add_bio_gripper` / `add_vacuum_gripper`).

Pick/place commands automatically:
1. **Open** gripper before arm motion (`pick`)
2. **Close** after grasp (force from RL → `/xarm/set_gripper_position`)
3. **Open** on place/release

Disable: `export PHYSICAL_AI_GRIPPER=0`

## 7. Customize
- **Different IP / namespace**: override `PHYSICAL_AI_TRAJECTORY_ACTION` if your controller name differs.
- **Isaac Sim**: `export PHYSICAL_AI_ISAAC_TWIN=1` and run `ros2 launch physical_ai_bringup twin.launch.py`.

## Files

- `config/robots/xarm6.py` — Python preset (auto-loaded)
- `robotics/ros2_ws/.../urdf/xarm6.urdf.xacro` — simplified model + optional official URDF
- `config/xarm6_moveit_controllers.yaml` — MoveIt controller reference
