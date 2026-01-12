from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# 정식 경로의 Tracker에서 Detection 클래스 import
from src.detectors.obstacle_tracker import Detection

RISK_SAFE = 0
RISK_CAUTION = 1
RISK_WARN = 2

RISK_NAME = {
    RISK_SAFE: "SAFE",
    RISK_CAUTION: "CAUTION",
    RISK_WARN: "WARN",
}

@dataclass
class RiskMetrics:
    risk_level: int
    risk_name: str
    score: float
    pttc_s: float
    dist_proxy: float
    closing_rate: float
    in_center: bool
    approaching: bool
    box_h: float
    area: float

@dataclass
class TrackState:
    dist_ema: Optional[float] = None
    prev_dist_ema: Optional[float] = None
    approach_streak: int = 0
    risk_level: int = RISK_SAFE
    hold_frames: int = 0
    last_seen_frame: int = 0

@dataclass
class RiskEngineConfig:
    center_band_ratio: float = 0.45
    near_center_band_ratio: float = 0.65
    ema_alpha: float = 0.35
    closing_rate_min: float = 0.02
    streak_warn: int = 8
    streak_caution: int = 4
    pttc_warn_s: float = 2.0
    pttc_caution_s: float = 4.0
    mega_close_boxh_ratio: float = 0.55
    mega_close_area_ratio: float = 0.35
    hysteresis_frames: int = 10
    stale_frames: int = 30
    class_weights: Dict[str, float] = field(default_factory=lambda: {"Person": 1.0, "Cart": 0.8})
    center_bonus: float = 0.2
    approach_bonus: float = 0.2

class RiskEngine:
    def __init__(self, cfg: RiskEngineConfig):
        self.cfg = cfg
        self.states: Dict[Tuple[str, int], TrackState] = {}

    def update(self, detections: List[Detection], frame_shape_hw: Tuple[int, int], frame_index: int, fps: float) -> Dict[int, RiskMetrics]:
        H, W = frame_shape_hw

        # hold 감소
        for st in self.states.values():
            if st.hold_frames > 0:
                st.hold_frames -= 1

        metrics_by_idx: Dict[int, RiskMetrics] = {}

        for idx, det in enumerate(detections):
            key = (det.cls_name, int(det.track_id))
            st = self.states.get(key)
            if st is None:
                st = TrackState(last_seen_frame=frame_index)
                self.states[key] = st
            st.last_seen_frame = frame_index

            x1, y1, x2, y2 = det.xyxy
            box_w = max(1.0, x2 - x1)
            box_h = max(1.0, y2 - y1)
            area = box_w * box_h
            cx = 0.5 * (x1 + x2)

            # 영역 판정
            center_left = (1.0 - self.cfg.center_band_ratio) * 0.5 * W
            center_right = W - center_left
            in_center = center_left <= cx <= center_right

            near_left = (1.0 - self.cfg.near_center_band_ratio) * 0.5 * W
            near_right = W - near_left
            in_near = near_left <= cx <= near_right

            # 거리/접근성 계산
            dist_proxy = self._dist_proxy(box_h, area, y2, H)
            alpha = self.cfg.ema_alpha
            st.prev_dist_ema = st.dist_ema
            st.dist_ema = dist_proxy if st.dist_ema is None else (alpha * dist_proxy + (1 - alpha) * st.dist_ema)

            closing_rate = 0.0
            if st.prev_dist_ema is not None and fps > 1e-6:
                closing_rate = max(0.0, (st.prev_dist_ema - st.dist_ema) * fps)

            approaching = closing_rate >= self.cfg.closing_rate_min
            if approaching and (in_center or in_near):
                st.approach_streak += 1
            else:
                st.approach_streak = max(0, st.approach_streak - 1)

            pttc_s = self._pttc_seconds(st.dist_ema, closing_rate)
            mega_close = (box_h / max(1.0, H) >= self.cfg.mega_close_boxh_ratio) or (area / max(1.0, W*H) >= self.cfg.mega_close_area_ratio)

            # 위험도 판정
            cand = RISK_SAFE
            if mega_close and in_near:
                cand = RISK_WARN
            elif in_center and st.approach_streak >= self.cfg.streak_warn and pttc_s <= self.cfg.pttc_warn_s:
                cand = RISK_WARN
            elif in_near and st.approach_streak >= self.cfg.streak_caution and pttc_s <= self.cfg.pttc_caution_s:
                cand = RISK_CAUTION

            # Hysteresis
            if cand > st.risk_level:
                st.risk_level = cand
                st.hold_frames = self.cfg.hysteresis_frames
            elif cand < st.risk_level and st.hold_frames <= 0:
                st.risk_level = cand

            score = self._score(det.cls_name, st.risk_level, st.dist_ema, pttc_s, in_center, approaching)

            metrics_by_idx[idx] = RiskMetrics(
                risk_level=st.risk_level,
                risk_name=RISK_NAME[st.risk_level],
                score=score,
                pttc_s=pttc_s,
                dist_proxy=float(st.dist_ema),
                closing_rate=float(closing_rate),
                in_center=in_center,
                approaching=approaching,
                box_h=float(box_h),
                area=float(area)
            )

        self._cleanup(frame_index)
        return metrics_by_idx

    def _cleanup(self, frame_index: int):
        stale = self.cfg.stale_frames
        to_del = [k for k, st in self.states.items() if (frame_index - st.last_seen_frame) > stale]
        for k in to_del:
            del self.states[k]

    @staticmethod
    def _dist_proxy(box_h, area, y2, H):
        return 0.60 * (1.0/max(1.0, box_h)) + 0.25 * (1.0/max(1.0, math.sqrt(area))) + 0.15 * max(0.0, (H-y2)/max(1.0, H))

    @staticmethod
    def _pttc_seconds(dist, cr):
        return float(dist / cr) if dist is not None and cr > 1e-9 else 1e9

    def _score(self, cls, lvl, dist, pttc, in_center, approaching):
        w = self.cfg.class_weights.get(cls, 1.0)
        s = lvl * 1000.0 + w * 100.0
        if dist: s += 30.0 * (1.0/max(1e-6, dist))
        if pttc < 1e6: s += 20.0 * (1.0/max(1e-3, pttc))
        if in_center: s += 50.0 * self.cfg.center_bonus
        if approaching: s += 50.0 * self.cfg.approach_bonus
        return s
