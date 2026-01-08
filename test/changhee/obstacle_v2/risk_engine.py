from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from detector import Detection

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
    boxh_ema: Optional[float] = None
    prev_boxh_ema: Optional[float] = None

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
    """
    추적된 객체(Track ID 유지)를 입력으로 받아 SAFE/CAUTION/WARN 판정.
    - 절대거리 대신 bbox 기반 dist_proxy (작을수록 가까움)
    - dist_proxy가 줄어들면 approaching
    - pTTC = dist_proxy / closing_rate (작을수록 임박)
    """

    def __init__(self, cfg: RiskEngineConfig):
        self.cfg = cfg
        self.states: Dict[Tuple[str, int], TrackState] = {}

    def update(
        self,
        detections: List[Detection],
        frame_shape_hw: Tuple[int, int],
        frame_index: int,
        fps: float,
    ) -> Dict[int, RiskMetrics]:
        H, W = frame_shape_hw

        # hold 감소(깜빡임 억제용)
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
            center_left = (1.0 - self.cfg.center_band_ratio) * 0.5 * W
            center_right = W - center_left
            in_center = center_left <= cx <= center_right

            near_left = (1.0 - self.cfg.near_center_band_ratio) * 0.5 * W
            near_right = W - near_left
            in_near_center = near_left <= cx <= near_right

            dist_proxy = self._dist_proxy(box_h=box_h, area=area, y2=y2, H=H)

            # EMA
            alpha = self.cfg.ema_alpha
            st.prev_dist_ema = st.dist_ema
            st.dist_ema = dist_proxy if st.dist_ema is None else (alpha * dist_proxy + (1 - alpha) * st.dist_ema)

            closing_rate = 0.0
            if st.prev_dist_ema is not None and fps > 1e-6:
                closing_rate = max(0.0, (st.prev_dist_ema - st.dist_ema) * fps)

            approaching = closing_rate >= self.cfg.closing_rate_min

            if approaching and (in_center or in_near_center):
                st.approach_streak += 1
            else:
                st.approach_streak = max(0, st.approach_streak - 1)

            pttc_s = self._pttc_seconds(dist_proxy=st.dist_ema, closing_rate=closing_rate)

            mega_close = (box_h / max(1.0, H)) >= self.cfg.mega_close_boxh_ratio or (area / max(1.0, (W * H))) >= self.cfg.mega_close_area_ratio

            candidate_level = RISK_SAFE
            if mega_close and in_near_center:
                candidate_level = RISK_WARN
            elif in_center and st.approach_streak >= self.cfg.streak_warn and pttc_s <= self.cfg.pttc_warn_s:
                candidate_level = RISK_WARN
            elif in_near_center and st.approach_streak >= self.cfg.streak_caution and pttc_s <= self.cfg.pttc_caution_s:
                candidate_level = RISK_CAUTION

            # hysteresis
            if candidate_level > st.risk_level:
                st.risk_level = candidate_level
                st.hold_frames = self.cfg.hysteresis_frames
            elif candidate_level < st.risk_level:
                if st.hold_frames <= 0:
                    st.risk_level = candidate_level

            score = self._score(
                cls_name=det.cls_name,
                risk_level=st.risk_level,
                dist_proxy=st.dist_ema,
                pttc_s=pttc_s,
                in_center=in_center,
                approaching=approaching,
            )

            metrics_by_idx[idx] = RiskMetrics(
                risk_level=st.risk_level,
                risk_name=RISK_NAME[st.risk_level],
                score=score,
                pttc_s=pttc_s,
                dist_proxy=float(st.dist_ema if st.dist_ema is not None else dist_proxy),
                closing_rate=float(closing_rate),
                in_center=bool(in_center),
                approaching=bool(approaching),
                box_h=float(box_h),
                area=float(area),
            )

        self._cleanup(frame_index)
        return metrics_by_idx

    def _cleanup(self, frame_index: int) -> None:
        stale = self.cfg.stale_frames
        to_del = [k for k, st in self.states.items() if (frame_index - st.last_seen_frame) > stale]
        for k in to_del:
            del self.states[k]

    @staticmethod
    def _dist_proxy(box_h: float, area: float, y2: float, H: float) -> float:
        inv_h = 1.0 / max(1.0, box_h)
        inv_sqrt_area = 1.0 / max(1.0, math.sqrt(area))
        bottom_gap = max(0.0, (H - y2) / max(1.0, H))
        return 0.60 * inv_h + 0.25 * inv_sqrt_area + 0.15 * bottom_gap

    @staticmethod
    def _pttc_seconds(dist_proxy: Optional[float], closing_rate: float) -> float:
        if dist_proxy is None or closing_rate <= 1e-9:
            return 1e9
        return float(dist_proxy / closing_rate)

    def _score(
        self,
        cls_name: str,
        risk_level: int,
        dist_proxy: Optional[float],
        pttc_s: float,
        in_center: bool,
        approaching: bool,
    ) -> float:
        w_cls = float(self.cfg.class_weights.get(cls_name, 1.0))
        closeness = 0.0 if dist_proxy is None else (1.0 / max(1e-6, dist_proxy))
        urgency = 0.0 if pttc_s > 1e6 else (1.0 / max(1e-3, pttc_s))

        score = 0.0
        score += risk_level * 1000.0
        score += w_cls * 100.0
        score += 30.0 * closeness
        score += 20.0 * urgency
        if in_center:
            score += 50.0 * self.cfg.center_bonus
        if approaching:
            score += 50.0 * self.cfg.approach_bonus
        return score
