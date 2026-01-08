from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import cv2

@dataclass
class WarnEvent:
    timestamp: str
    frame_index: int
    track_id: int
    cls_name: str
    score: float
    pttc_s: float
    dist_proxy: float
    closing_rate: float
    xyxy: Tuple[float, float, float, float]

class EventLogger:
    def __init__(self, out_dir: str, csv_name="events.csv", save_snapshots=True):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.snap_dir = self.out_dir / "snapshots"
        if save_snapshots: self.snap_dir.mkdir(parents=True, exist_ok=True)
        self.save_snapshots = save_snapshots

        self.csv_path = self.out_dir / csv_name
        self._f = open(self.csv_path, "a", newline="", encoding="utf-8")
        self._w = csv.writer(self._f)
        if self.csv_path.stat().st_size == 0:
            self._w.writerow(["timestamp", "frame_index", "track_id", "class", "score", "pttc_s", "dist_proxy", "closing_rate", "x1", "y1", "x2", "y2"])
            self._f.flush()

    def log_warn(self, ev: WarnEvent, frame):
        self._w.writerow([ev.timestamp, ev.frame_index, ev.track_id, ev.cls_name, f"{ev.score:.3f}", f"{ev.pttc_s:.3f}", f"{ev.dist_proxy:.6f}", f"{ev.closing_rate:.6f}", *[f"{x:.1f}" for x in ev.xyxy]])
        self._f.flush()
        if self.save_snapshots and frame is not None:
            ts = ev.timestamp.replace(":", "-")
            cv2.imwrite(str(self.snap_dir / f"warn_{ts}_f{ev.frame_index}_id{ev.track_id}.jpg"), frame)

    def close(self):
        self._f.close()

    @staticmethod
    def now_iso():
        return datetime.now().isoformat(timespec="seconds")
