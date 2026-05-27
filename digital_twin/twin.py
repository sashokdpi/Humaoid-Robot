"""Digital twin sync: real robot state mirrored into simulation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from brain_ai.types import MotionPlan, RobotState
from brain_ai.world_model.model import WorldModelState
from config.settings import Settings


@dataclass
class TwinState:
    robot: RobotState
    world: WorldModelState
    validated: bool = False
    notes: list[str] = field(default_factory=list)


class DigitalTwin(ABC):
    @abstractmethod
    def sync(self, robot: RobotState, world: WorldModelState) -> TwinState:
        raise NotImplementedError

    @abstractmethod
    def validate_motion(self, plan: MotionPlan) -> bool:
        raise NotImplementedError


class SimulatedDigitalTwin(DigitalTwin):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings
        self.twin_state: TwinState | None = None
        self._isaac = None
        if settings and settings.isaac_twin_enabled:
            try:
                from digital_twin.isaac_bridge import IsaacTwinBridge

                self._isaac = IsaacTwinBridge(settings)
            except ImportError:
                pass

    def sync(self, robot: RobotState, world: WorldModelState) -> TwinState:
        self.twin_state = TwinState(robot=robot, world=world, validated=False)
        self.twin_state.notes.append("In-memory twin synced with robot + world model")
        return self.twin_state

    def validate_motion(self, plan: MotionPlan) -> bool:
        if self.twin_state is None:
            return False
        if not plan.collision_free:
            self.twin_state.notes.append("Collision detected in twin")
            return False

        if self._isaac is not None:
            ok, msg = self._isaac.validate_motion(plan)
            self.twin_state.notes.append(msg)
            if not ok:
                return False

        self.twin_state.validated = True
        self.twin_state.notes.append("Trajectory validated (sim + optional Isaac)")
        return True


class IsaacDigitalTwin(DigitalTwin):
    """Hardware mode: prefer Isaac validation when twin stack is up."""

    def __init__(self, settings: Settings) -> None:
        from digital_twin.isaac_bridge import IsaacTwinBridge

        self.settings = settings
        self._isaac = IsaacTwinBridge(settings)
        self.twin_state: TwinState | None = None

    def sync(self, robot: RobotState, world: WorldModelState) -> TwinState:
        self.twin_state = TwinState(robot=robot, world=world)
        self.twin_state.notes.append("Isaac digital twin sync (ROS2 bridge)")
        return self.twin_state

    def validate_motion(self, plan: MotionPlan) -> bool:
        ok, msg = self._isaac.validate_motion(plan)
        if self.twin_state:
            self.twin_state.notes.append(msg)
            self.twin_state.validated = ok
        return ok


def build_digital_twin(settings: Settings) -> DigitalTwin:
    if settings.mode.value == "hardware" and settings.isaac_twin_enabled:
        return IsaacDigitalTwin(settings)
    return SimulatedDigitalTwin(settings)
