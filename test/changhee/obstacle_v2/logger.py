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
    def __init__(self, out_dir: str, csv_name: str = "events.csv", save_snapshots: bool = True) -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.csv_path = self.out_dir / csv_name
        self.save_snapshots = save_snapshots
        self.snap_dir = self.out_dir / "snapshots"
        if self.save_snapshots:
            self.snap_dir.mkdir(parents=True, exist_ok=True)

        self._csv_file = open(self.csv_path, "a", newline="", encoding="utf-8")
        self._writer = csv.writer(self._csv_file)

        if self.csv_path.stat().st_size == 0:
            self._writer.writerow([
                "timestamp", "frame_index", "track_id", "class",
                "score", "pttc_s", "dist_proxy", "closing_rate",
                "x1", "y1", "x2", "y2",
            ])
            self._csv_file.flush()

    def log_warn(self, event: WarnEvent, frame_bgr) -> Optional[str]:
        self._writer.writerow([
            event.timestamp, event.frame_index, event.track_id, event.cls_name,
            f"{event.score:.3f}", f"{event.pttc_s:.3f}", f"{event.dist_proxy:.6f}", f"{event.closing_rate:.6f}",
            f"{event.xyxy[0]:.1f}", f"{event.xyxy[1]:.1f}", f"{event.xyxy[2]:.1f}", f"{event.xyxy[3]:.1f}",
        ])
        self._csv_file.flush()

        snap_path = None
        if self.save_snapshots and frame_bgr is not None:
            ts = event.timestamp.replace(":", "-")
            snap_path = str(self.snap_dir / f"warn_{ts}_f{event.frame_index}_id{event.track_id}.jpg")
            cv2.imwrite(snap_path, frame_bgr)
        return snap_path

    def close(self) -> None:
        try:
            self._csv_file.flush()
        finally:
            self._csv_file.close()

    @staticmethod
    def now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")
