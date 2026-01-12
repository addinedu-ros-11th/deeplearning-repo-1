# test/changhee/obstacle_person_tune/patch_rules.py
from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Tuple


def unique_track_id_for_untracked(frame_index: int, det_index: int, base: int = -1_000_000) -> int:
    """
    track_id=-1 같은 untracked가 한 버킷에 섞여 상태가 튀는 걸 방지:
    프레임/인덱스 기반 유니크 음수 ID로 치환.
    """
    return base - frame_index * 1000 - det_index


def is_border_box(x1: float, y1: float, x2: float, y2: float, W: int, H: int, margin_ratio: float = 0.01) -> bool:
    mx = margin_ratio * W
    my = margin_ratio * H
    return (x1 <= mx) or (x2 >= (W - mx)) or (y1 <= my) or (y2 >= (H - my))


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


def clone_with_track_id(det: Any, new_tid: int) -> Any:
    """
    dev Detection이 dataclass면 replace가 되고,
    아니면 생성자 기반으로 새로 만든다.
    """
    try:
        return replace(det, track_id=int(new_tid))
    except Exception:
        # fallback: __class__ constructor (track_id, cls_id, cls_name, conf, xyxy)
        C = det.__class__
        return C(
            int(new_tid),
            int(getattr(det, "cls_id", -1)),
            str(getattr(det, "cls_name", "")),
            float(getattr(det, "conf", 0.0)),
            tuple(getattr(det, "xyxy", (0, 0, 0, 0))),
        )


def strict_person_warn_gate(
    det: Any,
    metric: Any,
    W: int,
    H: int,
    warn_pttc_s: float,
    border_margin_ratio: float,
) -> bool:
    """
    'Person WARN 허용 조건'을 강제:
    approaching + in_center + pTTC 감소(=pTTC가 충분히 작음) + edge 아님
    """
    cls_name = get_cls_name(det)
    if cls_name != "Person":
        return True  # 사람 아닌 건 개입 안 함(원하면 확장 가능)

    x1, y1, x2, y2 = get_xyxy(det)
    if is_border_box(x1, y1, x2, y2, W, H, border_margin_ratio):
        return False

    approaching = bool(getattr(metric, "approaching", False))
    in_center = bool(getattr(metric, "in_center", False))
    pttc_s = float(getattr(metric, "pttc_s", 1e9))

    if not approaching:
        return False
    if not in_center:
        return False
    if pttc_s > warn_pttc_s:
        return False
    return True


def downgrade_level(level: int, target: int) -> int:
    return target if level > target else level


class PersonWarnStreak:
    """
    엔진 내부 streak가 near-center에서도 쌓이거나,
    박스 흔들림으로 approaching/pttc가 튀는 걸 막기 위한 '로컬 연속 프레임 게이트'
    """
    def __init__(self, need_frames: int = 3) -> None:
        self.need_frames = need_frames
        self._streak: Dict[int, int] = {}

    def step(self, track_id: int, is_warn_candidate: bool) -> bool:
        cur = self._streak.get(track_id, 0)
        if is_warn_candidate:
            cur += 1
        else:
            cur = max(0, cur - 1)
        self._streak[track_id] = cur
        return cur >= self.need_frames
