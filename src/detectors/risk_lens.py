from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, List, Tuple, Optional


RISK_SAFE = 0
RISK_CAUTION = 1
RISK_WARN = 2
RISK_NAME = {0: "SAFE", 1: "CAUTION", 2: "WARN"}


def unique_track_id_for_untracked(frame_index: int, det_index: int, base: int = -1_000_000) -> int:
    return base - frame_index * 1000 - det_index


def get_xyxy(det: Any) -> Tuple[float, float, float, float]:
    xyxy = getattr(det, "xyxy", None)
    if xyxy is None:
        return (0.0, 0.0, 0.0, 0.0)
    x1, y1, x2, y2 = xyxy
    return float(x1), float(y1), float(x2), float(y2)


def get_cls_name(det: Any) -> str:
    return str(getattr(det, "cls_name", ""))


def get_track_id(det: Any) -> int:
    return int(getattr(det, "track_id", -1))


def get_conf(det: Any) -> float:
    return float(getattr(det, "conf", 0.0))


def clone_with_track_id(det: Any, new_tid: int) -> Any:
    try:
        return replace(det, track_id=int(new_tid))
    except Exception:
        C = det.__class__
        return C(
            int(new_tid),
            int(getattr(det, "cls_id", -1)),
            str(getattr(det, "cls_name", "")),
            float(getattr(det, "conf", 0.0)),
            tuple(getattr(det, "xyxy", (0, 0, 0, 0))),
        )


def is_border_box(x1: float, y1: float, x2: float, y2: float, W: int, H: int, margin_ratio: float = 0.01) -> bool:
    mx = margin_ratio * W
    my = margin_ratio * H
    return (x1 <= mx) or (x2 >= (W - mx)) or (y1 <= my) or (y2 >= (H - my))


def geom_from_xyxy(x1: float, y1: float, x2: float, y2: float, W: int, H: int) -> Dict[str, float]:
    w = max(1.0, x2 - x1)
    h = max(1.0, y2 - y1)
    cx = 0.5 * (x1 + x2)

    bw = w / max(1.0, W)
    hh = h / max(1.0, H)
    ar = (w * h) / max(1.0, (W * H))
    wh = w / max(1e-6, h)
    cxn = cx / max(1.0, W)
    close = min(bw, hh)

    return {"bw": bw, "hh": hh, "ar": ar, "wh": wh, "cxn": cxn, "close": close}


@dataclass
class MotionState:
    ar_ema: float = 0.0
    prev_ar_ema: float = 0.0
    cx_ema: float = 0.0
    prev_cx_ema: float = 0.0
    initialized: bool = False


class MotionEstimator:
    def __init__(self, alpha: float = 0.40):
        self.alpha = float(alpha)
        self.states: Dict[int, MotionState] = {}

    def update(self, track_id: int, ar: float, cxn: float, fps: float) -> Tuple[float, float, float]:
        st = self.states.get(track_id)
        if st is None:
            st = MotionState()
            self.states[track_id] = st

        if not st.initialized:
            st.ar_ema = float(ar)
            st.prev_ar_ema = float(ar)
            st.cx_ema = float(cxn)
            st.prev_cx_ema = float(cxn)
            st.initialized = True
            return st.ar_ema, 0.0, 0.0

        a = self.alpha
        st.prev_ar_ema = st.ar_ema
        st.prev_cx_ema = st.cx_ema

        st.ar_ema = a * float(ar) + (1 - a) * st.ar_ema
        st.cx_ema = a * float(cxn) + (1 - a) * st.cx_ema

        fps = max(1e-6, float(fps))
        ar_rate = (st.ar_ema - st.prev_ar_ema) * fps
        cx_speed = abs(st.cx_ema - st.prev_cx_ema) * fps
        return st.ar_ema, float(ar_rate), float(cx_speed)


class StreakGate:
    def __init__(self, need_frames: int = 3):
        self.need_frames = int(need_frames)
        self._streak: Dict[int, int] = {}

    def step(self, track_id: int, ok: bool) -> bool:
        cur = self._streak.get(track_id, 0)
        cur = cur + 1 if ok else max(0, cur - 1)
        self._streak[track_id] = cur
        return cur >= self.need_frames


def box_quality_ok(
    cls_name: str,
    conf: float,
    bw: float,
    hh: float,
    wh: float,
    border: bool,
    close: float,
    min_conf_person: float,
    min_conf_cart: float,
    person_wh_max: float,
    cart_wh_min: float,
    cart_wh_max: float,
    border_close_min: float,
) -> bool:
    if cls_name == "Person":
        if conf < min_conf_person:
            return False
        if wh > person_wh_max:
            return False
        if border and close < border_close_min:
            return False
        return True

    if cls_name == "Cart":
        if conf < min_conf_cart:
            return False
        if wh < cart_wh_min or wh > cart_wh_max:
            return False
        if border and close < border_close_min:
            return False
        return True

    if border and close < border_close_min:
        return False
    return True


def pttc_area(ar_ema: float, ar_rate: float, target_ar: float) -> float:
    if ar_rate <= 1e-6:
        return 1e9
    remain = max(0.0, float(target_ar) - float(ar_ema))
    return remain / max(1e-6, float(ar_rate))


@dataclass
class RiskLensConfig:
    # 공통
    border_margin: float = 0.01
    motion_alpha: float = 0.40

    # approaching 재정의
    min_area_rate: float = 0.020
    max_cx_speed: float = 0.45
    min_ar_for_motion: float = 0.020

    # 박스 품질
    min_conf_person: float = 0.25
    min_conf_cart: float = 0.25
    person_wh_max: float = 1.60
    cart_wh_min: float = 0.40
    cart_wh_max: float = 4.50
    border_close_min: float = 0.18

    # 정지 초근접 WARN 옵션
    allow_static_person_warn: bool = False
    allow_static_cart_warn: bool = False

    person_caution_close: float = 0.22
    person_static_warn_close: float = 0.48
    cart_caution_close: float = 0.26
    cart_static_warn_close: float = 0.60
    cart_caution_require_center: bool = False

    # WARN 게이트
    person_warn_frames: int = 3
    cart_warn_frames: int = 3

    person_warn_ar_target: float = 0.30
    cart_warn_ar_target: float = 0.35

    person_warn_ttc_s: float = 2.0
    cart_warn_ttc_s: float = 2.0

    person_warn_close_min: float = 0.30
    cart_warn_close_min: float = 0.34


class RiskLens:
    def __init__(self, cfg: Optional[RiskLensConfig] = None):
        self.cfg = cfg or RiskLensConfig()
        self.motion = MotionEstimator(alpha=self.cfg.motion_alpha)
        self.person_warn_gate = StreakGate(need_frames=self.cfg.person_warn_frames)
        self.cart_warn_gate = StreakGate(need_frames=self.cfg.cart_warn_frames)

    def fix_untracked(self, detections: List[Any], frame_index: int) -> List[Any]:
        dets_fixed: List[Any] = []
        for i, det in enumerate(detections):
            tid = get_track_id(det)
            if tid < 0:
                tid = unique_track_id_for_untracked(frame_index, i)
                det = clone_with_track_id(det, tid)
            dets_fixed.append(det)
        return dets_fixed

    def apply(self, detections: List[Any], H: int, W: int, fps: float, center_band_ratio: float) -> Dict[int, int]:
        patched_levels: Dict[int, int] = {}

        def in_center(cx: float) -> bool:
            left = (1.0 - float(center_band_ratio)) * 0.5 * W
            right = W - left
            return left <= cx <= right

        for i, det in enumerate(detections):
            cls_name = get_cls_name(det)
            conf = get_conf(det)
            x1, y1, x2, y2 = get_xyxy(det)

            border = is_border_box(x1, y1, x2, y2, W, H, self.cfg.border_margin)
            g = geom_from_xyxy(x1, y1, x2, y2, W, H)
            bw, hh, ar, wh, cxn, close = g["bw"], g["hh"], g["ar"], g["wh"], g["cxn"], g["close"]
            inc = in_center(cxn * W)

            ok_box = box_quality_ok(
                cls_name=cls_name, conf=conf,
                bw=bw, hh=hh, wh=wh,
                border=border, close=close,
                min_conf_person=self.cfg.min_conf_person,
                min_conf_cart=self.cfg.min_conf_cart,
                person_wh_max=self.cfg.person_wh_max,
                cart_wh_min=self.cfg.cart_wh_min,
                cart_wh_max=self.cfg.cart_wh_max,
                border_close_min=self.cfg.border_close_min,
            )
            if not ok_box:
                patched_levels[i] = RISK_SAFE
                continue

            tid = get_track_id(det)
            ar_ema, ar_rate, cx_speed = self.motion.update(tid, ar, cxn, fps)

            approach_est = (
                (ar_ema >= self.cfg.min_ar_for_motion) and
                (ar_rate >= self.cfg.min_area_rate) and
                (cx_speed <= self.cfg.max_cx_speed)
            )

            if cls_name == "Person":
                warn_pttc = pttc_area(ar_ema, ar_rate, self.cfg.person_warn_ar_target)
                warn_candidate = approach_est and inc and (close >= self.cfg.person_warn_close_min) and (warn_pttc <= self.cfg.person_warn_ttc_s)
                warn_ok = self.person_warn_gate.step(tid, warn_candidate)

                lvl = RISK_SAFE
                if warn_ok:
                    lvl = RISK_WARN
                else:
                    if close >= self.cfg.person_caution_close:
                        lvl = RISK_CAUTION

                    if self.cfg.allow_static_person_warn and (close >= self.cfg.person_static_warn_close):
                        super_close = close >= self.cfg.person_static_warn_close * 1.10
                        if (not border) or super_close:
                            lvl = RISK_WARN

                patched_levels[i] = int(lvl)

            elif cls_name == "Cart":
                warn_pttc = pttc_area(ar_ema, ar_rate, self.cfg.cart_warn_ar_target)
                warn_candidate = approach_est and inc and (close >= self.cfg.cart_warn_close_min) and (warn_pttc <= self.cfg.cart_warn_ttc_s)
                warn_ok = self.cart_warn_gate.step(tid, warn_candidate)

                lvl = RISK_SAFE
                if warn_ok:
                    lvl = RISK_WARN
                else:
                    allow_caution = True
                    if self.cfg.cart_caution_require_center:
                        allow_caution = bool(inc)
                    if allow_caution and (close >= self.cfg.cart_caution_close):
                        lvl = RISK_CAUTION

                    if self.cfg.allow_static_cart_warn and (close >= self.cfg.cart_static_warn_close):
                        super_close = close >= self.cfg.cart_static_warn_close * 1.10
                        if (not border) or super_close:
                            lvl = RISK_WARN

                patched_levels[i] = int(lvl)

            else:
                patched_levels[i] = RISK_SAFE

        return patched_levels
