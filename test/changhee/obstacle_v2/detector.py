from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterator, List, Union

import numpy as np
from ultralytics import YOLO


@dataclass
class Detection:
    """One tracked detection on a single frame."""
    track_id: int
    cls_id: int
    cls_name: str
    conf: float
    xyxy: tuple[float, float, float, float]  # (x1, y1, x2, y2)


@dataclass
class FrameDetections:
    """Detections for a single frame."""
    frame_index: int
    timestamp_s: float
    fps: float
    frame_bgr: np.ndarray
    detections: List[Detection]


def _as_numpy(x):
    """Convert torch tensor / numpy / list to numpy array without importing torch."""
    if x is None:
        return None
    if hasattr(x, "detach"):
        x = x.detach()
    if hasattr(x, "cpu"):
        x = x.cpu()
    if hasattr(x, "numpy"):
        return x.numpy()
    return np.asarray(x)


class YoloTrackerDetector:
    """
    Ultralytics YOLO track wrapper:
    - stream=True 로 프레임 단위 결과를 받음
    - boxes.id(Track ID)가 있으면 동일 객체를 이어줌
    """

    def __init__(
        self,
        weights: str,
        tracker: str = "bytetrack.yaml",
        conf: float = 0.35,
        iou: float = 0.5,
        imgsz: int = 640,
        device: Union[str, int] = "0",
        persist: bool = True,
        verbose: bool = False,
    ) -> None:
        self.weights = weights
        self.tracker = tracker
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz
        self.device = device
        self.persist = persist
        self.verbose = verbose

        self.model = YOLO(weights)

    def stream(self, source: Union[int, str]) -> Iterator[FrameDetections]:
        results_iter = self.model.track(
            source=source,
            stream=True,
            persist=self.persist,
            tracker=self.tracker,
            conf=self.conf,
            iou=self.iou,
            imgsz=self.imgsz,
            device=self.device,
            verbose=self.verbose,
            show=False,
            save=False,
        )

        t0 = time.time()
        last_t = t0
        fps_est = 0.0
        frame_index = 0

        for r in results_iter:
            now = time.time()
            dt = max(1e-6, now - last_t)
            inst_fps = 1.0 / dt
            fps_est = inst_fps if fps_est <= 0 else (0.9 * fps_est + 0.1 * inst_fps)
            last_t = now

            frame = getattr(r, "orig_img", None)
            if frame is None:
                continue

            detections = self._parse_results(r)

            yield FrameDetections(
                frame_index=frame_index,
                timestamp_s=now - t0,
                fps=fps_est,
                frame_bgr=frame,
                detections=detections,
            )
            frame_index += 1

    def _parse_results(self, r) -> List[Detection]:
        boxes = getattr(r, "boxes", None)
        if boxes is None:
            return []

        xyxy = _as_numpy(getattr(boxes, "xyxy", None))
        conf = _as_numpy(getattr(boxes, "conf", None))
        cls = _as_numpy(getattr(boxes, "cls", None))
        ids = _as_numpy(getattr(boxes, "id", None))

        if xyxy is None or len(xyxy) == 0:
            return []

        names: Dict[int, str] = getattr(self.model, "names", None) or getattr(r, "names", {})

        out: List[Detection] = []
        n = len(xyxy)
        for i in range(n):
            cls_id = int(cls[i])
            cls_name = names.get(cls_id, str(cls_id))
            conf_i = float(conf[i]) if conf is not None and len(conf) > i else 0.0
            x1, y1, x2, y2 = map(float, xyxy[i].tolist())

            track_id = -1 if ids is None else int(ids[i])

            out.append(
                Detection(
                    track_id=track_id,
                    cls_id=cls_id,
                    cls_name=cls_name,
                    conf=conf_i,
                    xyxy=(x1, y1, x2, y2),
                )
            )
        return out
