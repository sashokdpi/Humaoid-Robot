from brain_ai.types import DetectedObject, Vector3


class SafetyAgent:
    """Pre-execution safety checks (human proximity, workspace limits)."""

    MIN_HUMAN_DISTANCE_M = 0.5

    def check(self, objects: list[DetectedObject], target_position: Vector3 | None) -> tuple[bool, str]:
        for obj in objects:
            if obj.label.lower() != "human":
                continue
            if target_position:
                dist = self._distance(obj.position, target_position)
                if dist < self.MIN_HUMAN_DISTANCE_M:
                    return False, f"Human too close to target ({dist:.2f} m)"
        return True, "Workspace safe"

    @staticmethod
    def _distance(a: Vector3, b: Vector3) -> float:
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5
