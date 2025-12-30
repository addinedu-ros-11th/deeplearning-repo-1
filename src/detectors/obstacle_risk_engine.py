# src/detectors/obstacle_risk_engine.py
import math
import time
import collections
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any

EPS = 1e-6
V_EPS = 1e-4


def _risk_rank(r: str) -> int:
    return {"SAFE": 0, "CAUTION": 1, "WARN": 2}.get(r, 0)


@dataclass
class RiskParams:
    # path gate
    center_band: float = 0.25
    center_only: bool = True  # True면 center band overlap로 in_path 판단

    # near gate
    h_caution: float = 0.18
    h_warn: float = 0.30

    # proxy TTC thresholds (person)
    pttc_warn: float = 2.2
    pttc_caution: float = 4.5

    # streak
    approach_streak_n: int = 5

    # smoothing
    dist_buf_n: int = 10
    vel_buf_n: int = 10

    # screen velocity thresholds (px/s)
    vx_eps_ratio: float = 0.03
    vy_eps_ratio: float = 0.03

    # growth approach thresholds
    grow_dh_pxps: float = 25.0
    grow_da_px2ps: float = 12000.0

    # mega-close (frame-covering)
    trunc_margin_px: int = 6
    mega_area_r: float = 0.55
    mega_edge_n: int = 2
    mega_confirm_n: int = 6

    # hysteresis
    warn_clear_n: int = 6
    caution_clear_n: int = 6

    # cleanup
    ttl_s: float = 3.0  # 오래 안 보이는 track state 자동 삭제


class TrackState:
    def __init__(self, p: RiskParams):
        self.dist_buf = collections.deque(maxlen=p.dist_buf_n)
        self.vel_buf = collections.deque(maxlen=p.vel_buf_n)
        self.vx_buf = collections.deque(maxlen=p.vel_buf_n)
        self.vy_buf = collections.deque(maxlen=p.vel_buf_n)

        self.prev_time: Optional[float] = None
        self.prev_dist: Optional[float] = None
        self.prev_cx: Optional[float] = None
        self.prev_cy: Optional[float] = None
        self.prev_h: Optional[float] = None
        self.prev_a: Optional[float] = None

        self.approach_streak: int = 0
        self.mega_streak: int = 0

        self.risk_state: str = "SAFE"
        self.warn_clear: int = 0
        self.caution_clear: int = 0

        self.last_seen: float = 0.0


class ObstacleRiskEngine:
    """
    사람(PERSON) track bbox들을 받아 SAFE/CAUTION/WARN을 계산.

    입력 dets 형식:
      [{"track_id": int, "xyxy": (x1,y1,x2,y2), "conf": float}, ...]
    출력:
      {"objects": [...], "best": {...} or None}
    """

    def __init__(self, params: Optional[RiskParams] = None):
        self.p = params or RiskParams()
        self._tracks: Dict[int, TrackState] = {}

    # --------- util ---------
    def _center_band_overlap(self, x1: int, x2: int, W: int) -> bool:
        lb = (0.5 - self.p.center_band / 2) * W
        rb = (0.5 + self.p.center_band / 2) * W
        return (x1 < rb) and (x2 > lb)

    def _direction_lcr(self, x1: int, x2: int, W: int) -> str:
        cx = (x1 + x2) / 2.0
        lb = (0.5 - self.p.center_band / 2) * W
        rb = (0.5 + self.p.center_band / 2) * W
        if cx < lb:
            return "L"
        if cx > rb:
            return "R"
        return "C"

    def _touched_edges(self, x1, y1, x2, y2, H, W) -> int:
        m = self.p.trunc_margin_px
        n = 0
        if x1 <= m: n += 1
        if y1 <= m: n += 1
        if x2 >= W - m: n += 1
        if y2 >= H - m: n += 1
        return n

    def _compute_dist_proxy(self, x1, y1, x2, y2, H, W):
        box_h = max(1, y2 - y1)
        box_w = max(1, x2 - x1)
        area = box_h * box_w

        p_h = 1.0 / (box_h + EPS)
        p_area = 1.0 / (math.sqrt(area) + EPS)
        p_y2 = max(1.0, H - y2) / float(H)

        dist = 0.60 * p_h + 0.25 * p_area + 0.15 * p_y2
        return dist, box_h, box_w, area

    def _cleanup(self, now_t: float):
        ttl = self.p.ttl_s
        dead = [tid for tid, st in self._tracks.items() if (now_t - st.last_seen) > ttl]
        for tid in dead:
            del self._tracks[tid]

    def _get_state(self, tid: int) -> TrackState:
        st = self._tracks.get(tid)
        if st is None:
            st = TrackState(self.p)
            self._tracks[tid] = st
        return st

    # --------- core ---------
    def update_many(self, dets: List[Dict[str, Any]], now_t: Optional[float], H: int, W: int) -> Dict[str, Any]:
        if now_t is None:
            now_t = time.time()

        self._cleanup(now_t)

        objects: List[Dict[str, Any]] = []
        best: Optional[Dict[str, Any]] = None
        best_score = -1.0

        for d in dets:
            tid = int(d.get("track_id", -1))
            x1, y1, x2, y2 = map(int, d["xyxy"])
            conf = float(d.get("conf", 1.0))

            info = self._update_one(tid, (x1, y1, x2, y2), now_t, H, W)
            obj = {
                "object_type": "PERSON",
                "track_id": tid,
                "bbox_xyxy": [x1, y1, x2, y2],
                "conf": conf,
                **info,
            }
            objects.append(obj)

            sev = _risk_rank(obj["risk"])
            dir_bonus = 1.0 if obj["dir"] == "C" else 0.2
            near_bonus = min(1.0, obj["h_ratio"] * 2.0) + (0.35 if obj["mega_close"] else 0.0) + (0.15 if obj["toward_center"] else 0.0)
            score = 10 * sev + 2 * dir_bonus + 2 * near_bonus

            if score > best_score:
                best_score = score
                best = obj

        return {"objects": objects, "best": best}

    def _update_one(self, tid: int, xyxy: Tuple[int, int, int, int], now_t: float, H: int, W: int) -> Dict[str, Any]:
        x1, y1, x2, y2 = xyxy

        # track state (tid<0이면 프레임 독립 처리)
        if tid >= 0:
            st = self._get_state(tid)
        else:
            st = TrackState(self.p)

        st.last_seen = now_t

        prev_t = st.prev_time
        prev_dist = st.prev_dist
        prev_cx = st.prev_cx
        prev_cy = st.prev_cy
        prev_h = st.prev_h
        prev_a = st.prev_a

        # measures
        d_raw, box_h, box_w, area = self._compute_dist_proxy(x1, y1, x2, y2, H, W)
        st.dist_buf.append(d_raw)
        d = sum(st.dist_buf) / len(st.dist_buf)

        h_ratio = box_h / float(H)
        y2_ratio = y2 / float(H)
        area_r = area / float(W * H)

        dirc = self._direction_lcr(x1, x2, W)
        in_path = self._center_band_overlap(x1, x2, W) if self.p.center_only else True

        close_caution = (h_ratio > self.p.h_caution)
        close_warn = (h_ratio > self.p.h_warn)

        # mega close
        edges = self._touched_edges(x1, y1, x2, y2, H, W)
        mega_close = (area_r > self.p.mega_area_r) and (edges >= self.p.mega_edge_n)
        risk_gate = in_path or mega_close

        if risk_gate and mega_close:
            st.mega_streak += 1
        else:
            st.mega_streak = 0

        # screen velocity
        cx = 0.5 * (x1 + x2)
        cy = 0.5 * (y1 + y2)

        vx = vy = 0.0
        speed_px = 0.0
        motion_dir = "--"
        VX_EPS = self.p.vx_eps_ratio * W
        VY_EPS = self.p.vy_eps_ratio * H

        if prev_t is not None and prev_cx is not None and prev_cy is not None:
            dt_xy = max(1e-3, now_t - prev_t)
            vx_raw = (cx - prev_cx) / dt_xy
            vy_raw = (cy - prev_cy) / dt_xy
            st.vx_buf.append(vx_raw)
            st.vy_buf.append(vy_raw)
            vx = sum(st.vx_buf) / len(st.vx_buf)
            vy = sum(st.vy_buf) / len(st.vy_buf)

            speed_px = math.sqrt(vx * vx + vy * vy)

            mx = "R" if vx > VX_EPS else ("L" if vx < -VX_EPS else "-")
            my = "D" if vy > VY_EPS else ("U" if vy < -VY_EPS else "-")
            motion_dir = f"{mx}{my}"

        toward_center = False
        if dirc == "L" and vx > VX_EPS:
            toward_center = True
        if dirc == "R" and vx < -VX_EPS:
            toward_center = True

        # approaching proxy + pTTC
        approaching_proxy = False
        closing_proxy = 0.0
        pttc = float("inf")

        if prev_t is not None and prev_dist is not None:
            dt = max(1e-3, now_t - prev_t)
            v_raw = (prev_dist - d) / dt
            st.vel_buf.append(v_raw)
            v = sum(st.vel_buf) / len(st.vel_buf)
            if v > V_EPS:
                approaching_proxy = True
                closing_proxy = v
                pttc = d / (v + EPS)

        # growth approach
        grow_approach = False
        if prev_t is not None and prev_h is not None and prev_a is not None:
            dt_g = max(1e-3, now_t - prev_t)
            dh = (box_h - prev_h) / dt_g
            da = (area - prev_a) / dt_g
            if dh > self.p.grow_dh_pxps or da > self.p.grow_da_px2ps:
                grow_approach = True

        approaching = approaching_proxy or grow_approach

        # streak
        st.approach_streak = (st.approach_streak + 1) if approaching else 0
        stable = (st.approach_streak >= self.p.approach_streak_n)

        # decide
        cand = "SAFE"
        if risk_gate and close_caution:
            cand = "CAUTION"

        if risk_gate and (st.mega_streak >= self.p.mega_confirm_n):
            cand = "WARN"
        else:
            pttc_warn_eff = self.p.pttc_warn * (1.15 if toward_center else 1.0)
            pttc_cau_eff = self.p.pttc_caution

            if risk_gate and approaching and stable and close_warn:
                if pttc < pttc_warn_eff:
                    cand = "WARN"
                elif (pttc == float("inf")) and grow_approach and mega_close:
                    cand = "WARN"

            if cand != "WARN" and risk_gate and approaching and close_caution:
                if pttc < pttc_cau_eff:
                    cand = "CAUTION"
                elif (pttc == float("inf")) and grow_approach:
                    cand = "CAUTION"

        # hysteresis
        prev_risk = st.risk_state
        if st.risk_state == "WARN":
            if cand == "WARN":
                st.warn_clear = 0
            else:
                st.warn_clear += 1
                if st.warn_clear >= self.p.warn_clear_n:
                    st.risk_state = cand
                    st.warn_clear = 0
        elif st.risk_state == "CAUTION":
            if cand == "WARN":
                st.risk_state = "WARN"
                st.caution_clear = 0
            elif cand == "SAFE":
                st.caution_clear += 1
                if st.caution_clear >= self.p.caution_clear_n:
                    st.risk_state = "SAFE"
                    st.caution_clear = 0
            else:
                st.caution_clear = 0
        else:
            st.risk_state = cand

        # update prevs
        st.prev_time = now_t
        st.prev_dist = d
        st.prev_cx, st.prev_cy = cx, cy
        st.prev_h, st.prev_a = float(box_h), float(area)

        return {
            "risk": st.risk_state,
            "prev_risk": prev_risk,
            "dir": dirc,
            "in_path": in_path,
            "risk_gate": risk_gate,
            "pttc": pttc,
            "closing_proxy": closing_proxy,
            "h_ratio": h_ratio,
            "y2_ratio": y2_ratio,
            "area_r": area_r,
            "vx": vx,
            "vy": vy,
            "speed_px": speed_px,
            "motion_dir": motion_dir,
            "toward_center": toward_center,
            "approach_streak": st.approach_streak,
            "mega_streak": st.mega_streak,
            "mega_close": mega_close,
            "grow_approach": grow_approach,
        }
