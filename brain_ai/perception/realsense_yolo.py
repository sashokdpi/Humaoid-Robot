"""RealSense D455 + YOLO perception (direct or via captured frame)."""

from __future__ import annotations

import colorsys
from typing import Any

from brain_ai.types import DetectedObject, PerceptionResult, Vector3
from config.settings import RealSenseSettings, Settings, YoloSettings

# COCO class names where index matches default YOLO training
_COCO_NAMES: dict[int, str] = {
    0: "person",
    39: "bottle",
    41: "cup",
    73: "book",
    76: "scissors",
}


class RealSenseYoloPerceptor:
    def __init__(self, settings: Settings) -> None:
        self.rs_settings: RealSenseSettings = settings.realsense
        self.yolo_settings: YoloSettings = settings.yolo
        self._pipeline = None
        self._align = None
        self._model = None

    def _init_realsense(self) -> None:
        if self._pipeline is not None:
            return
        import pyrealsense2 as rs

        pipeline = rs.pipeline()
        config = rs.config()
        if self.rs_settings.serial:
            config.enable_device(self.rs_settings.serial)
        config.enable_stream(
            rs.stream.color,
            self.rs_settings.color_width,
            self.rs_settings.color_height,
            rs.format.bgr8,
            self.rs_settings.fps,
        )
        config.enable_stream(
            rs.stream.depth,
            self.rs_settings.color_width,
            self.rs_settings.color_height,
            rs.format.z16,
            self.rs_settings.fps,
        )
        pipeline.start(config)
        self._pipeline = pipeline
        if self.rs_settings.align_depth:
            self._align = rs.align(rs.stream.color)

    def _init_yolo(self) -> Any:
        if self._model is not None:
            return self._model
        from ultralytics import YOLO

        device = self.yolo_settings.device
        if device == "auto":
            try:
                import torch

                device = "cuda:0" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        self._model = YOLO(self.yolo_settings.model_path)
        self._yolo_device = device
        return self._model

    def perceive(self) -> PerceptionResult:
        self._init_realsense()
        self._init_yolo()

        import numpy as np
        import pyrealsense2 as rs

        frames = self._pipeline.wait_for_frames()
        if self._align:
            frames = self._align.process(frames)
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        if not color_frame or not depth_frame:
            raise RuntimeError("RealSense returned empty frames")

        color = np.asanyarray(color_frame.get_data())
        depth = np.asanyarray(depth_frame.get_data())
        intr = depth_frame.profile.as_video_stream_profile().intrinsics

        results = self._model.predict(
            color,
            conf=self.yolo_settings.confidence,
            device=self._yolo_device,
            verbose=False,
        )[0]

        objects: list[DetectedObject] = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = results.names.get(cls_id, _COCO_NAMES.get(cls_id, "object"))
            if self.yolo_settings.target_classes and label not in self.yolo_settings.target_classes:
                continue

            xyxy = box.xyxy[0].tolist()
            cx = int((xyxy[0] + xyxy[2]) / 2)
            cy = int((xyxy[1] + xyxy[3]) / 2)
            cx = max(0, min(cx, depth.shape[1] - 1))
            cy = max(0, min(cy, depth.shape[0] - 1))

            depth_m = depth[cy, cx] * depth_frame.get_units()
            if depth_m <= 0:
                continue

            point = rs.rs2_deproject_pixel_to_point(intr, [cx, cy], depth_m)
            # Camera frame: x right, y down, z forward -> map to robot base approximation
            position = Vector3(x=float(point[2]), y=float(-point[0]), z=float(-point[1]))
            color_name = _dominant_color_name(color, xyxy)
            conf = float(box.conf[0])
            objects.append(
                DetectedObject(
                    label=label if label != "person" else "human",
                    color=color_name,
                    position=position,
                    confidence=conf,
                    bbox=xyxy,
                )
            )

        labels = ", ".join(f"{o.color or ''} {o.label}".strip() for o in objects) or "no objects"
        free_space = 1.0 - min(len(objects) * 0.12, 0.8)
        return PerceptionResult(
            objects=objects,
            scene_summary=f"RealSense+YOLO: {labels}",
            free_space_ratio=free_space,
        )

    def close(self) -> None:
        if self._pipeline is not None:
            self._pipeline.stop()
            self._pipeline = None


def _dominant_color_name(bgr_image: Any, bbox: list[float]) -> str | None:
    import numpy as np

    x1, y1, x2, y2 = [int(v) for v in bbox]
    crop = bgr_image[y1:y2, x1:x2]
    if crop.size == 0:
        return None
    mean = crop.reshape(-1, 3).mean(axis=0)
    b, g, r = mean / 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if v < 0.2:
        return "dark"
    if s < 0.15:
        return "gray"
    if h < 0.05 or h > 0.95:
        return "red"
    if h < 0.15:
        return "orange"
    if h < 0.45:
        return "yellow" if h < 0.2 else "green"
    if h < 0.65:
        return "blue"
    return "purple"
