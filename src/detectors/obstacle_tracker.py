from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Iterator, List, Union
import numpy as np
from ultralytics import YOLO

@dataclass
class Detection:
    track_id: int
    cls_id: int
    cls_name: str
    conf: float
    xyxy: tuple[float, float, float, float]

@dataclass
class FrameDetections:
    frame_index: int
    timestamp_s: float
    fps: float
    frame_bgr: np.ndarray
    detections: List[Detection]

def _as_numpy(x):
    if x is None: return None
    if hasattr(x, "detach"): x = x.detach()
    if hasattr(x, "cpu"): x = x.cpu()
    if hasattr(x, "numpy"): return x.numpy()
    return np.asarray(x)

class YoloTrackerDetector:
    def __init__(self, weights: str, tracker: str = "bytetrack.yaml", conf: float = 0.35, iou: float = 0.5, imgsz: int = 640, device="0", persist=True, verbose=False):
        self.model = YOLO(weights)
        self.params = {"tracker": tracker, "conf": conf, "iou": iou, "imgsz": imgsz, "device": device, "persist": persist, "verbose": verbose}

    def stream(self, source) -> Iterator[FrameDetections]:
        results = self.model.track(source=source, stream=True, show=False, save=False, **self.params)
        t0 = time.time()
        last_t = t0
        fps_est = 0.0
        idx = 0

        for r in results:
            now = time.time()
            dt = max(1e-6, now - last_t)
            fps_est = (1.0/dt) if fps_est <= 0 else (0.9*fps_est + 0.1*(1.0/dt))
            last_t = now

            frame = getattr(r, "orig_img", None)
            if frame is None: continue

            dets = self._parse(r)
            yield FrameDetections(idx, now-t0, fps_est, frame, dets)
            idx += 1

    def _parse(self, r) -> List[Detection]:
        boxes = getattr(r, "boxes", None)
        if boxes is None: return []
        xyxy = _as_numpy(getattr(boxes, "xyxy", None))
        if xyxy is None or len(xyxy) == 0: return []

        ids = _as_numpy(getattr(boxes, "id", None))
        conf = _as_numpy(getattr(boxes, "conf", None))
        cls = _as_numpy(getattr(boxes, "cls", None))
        names = getattr(self.model, "names", {}) or {}

        out = []
        for i in range(len(xyxy)):
            tid = int(ids[i]) if ids is not None else -1
            c_id = int(cls[i])
            out.append(Detection(tid, c_id, names.get(c_id, str(c_id)), float(conf[i]) if conf is not None else 0.0, tuple(map(float, xyxy[i]))))
        return out
