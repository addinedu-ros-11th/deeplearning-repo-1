# test/changhee/obstacle_person_tune/run_webcam_patch.py
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

import cv2
import yaml

from patch_rules import (
    PersonWarnStreak,
    clone_with_track_id,
    get_cls_name,
    get_track_id,
    get_xyxy,
    strict_person_warn_gate,
    unique_track_id_for_untracked,
)

# repo root를 sys.path에 넣어 dev 모듈 import 안정화
REPO_ROOT = Path(__file__).resolve().parents[3]  # .../test/changhee/obstacle_person_tune/ -> repo
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _parse_source(src: str) -> Union[int, str]:
    return int(src) if src.isdigit() else src


def _color_for(level: int) -> tuple[int, int, int]:
    # BGR
    if level >= 2:
        return (0, 0, 255)
    if level == 1:
        return (0, 255, 255)
    return (0, 255, 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, default="configs/model_config.yaml")
    ap.add_argument("--source", type=str, default="0")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--person_warn_frames", type=int, default=3, help="Person WARN 연속 프레임 게이트(기본 3)")
    ap.add_argument("--border_margin", type=float, default=0.01, help="edge 판정 마진 비율(기본 0.01)")
    args = ap.parse_args()

    cfg: Dict[str, Any] = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    # --- dev 모듈 import (그대로 사용) ---
    tracker_mod = importlib.import_module("src.detectors.obstacle_tracker")
    risk_mod = importlib.import_module("src.detectors.risk_engine")

    YoloTrackerDetector = getattr(tracker_mod, "YoloTrackerDetector")
    RiskEngine = getattr(risk_mod, "RiskEngine")
    RiskEngineConfig = getattr(risk_mod, "RiskEngineConfig")

    # risk level 상수 (없으면 fallback)
    RISK_SAFE = int(getattr(risk_mod, "RISK_SAFE", 0))
    RISK_CAUTION = int(getattr(risk_mod, "RISK_CAUTION", 1))
    RISK_WARN = int(getattr(risk_mod, "RISK_WARN", 2))
    RISK_NAME = getattr(risk_mod, "RISK_NAME", {0: "SAFE", 1: "CAUTION", 2: "WARN"})

    # --- instantiate ---
    detector = YoloTrackerDetector(
        weights=cfg["models"]["weights"],
        **cfg.get("tracking", {}),
        **cfg.get("inference", {}),
    )
    engine = RiskEngine(RiskEngineConfig(**cfg.get("risk", {})))

    # thresholds (없으면 기본)
    warn_pttc_s = float(cfg.get("risk", {}).get("pttc_warn_s", 2.0))
    border_margin_ratio = float(cfg.get("risk", {}).get("border_margin_ratio", args.border_margin))

    person_warn_gate = PersonWarnStreak(need_frames=int(args.person_warn_frames))

    src = _parse_source(args.source)

    while True:
        # stream iterator 재시작 안전장치(웹캠 끊김 대비)
        for fd in detector.stream(src):
            frame = fd.frame_bgr.copy()
            H, W = frame.shape[:2]

            # 1) track_id=-1 섞임 방지: untracked는 유니크 id로 치환
            dets_fixed: List[Any] = []
            for i, det in enumerate(fd.detections):
                tid = get_track_id(det)
                if tid < 0:
                    tid = unique_track_id_for_untracked(fd.frame_index, i)
                    det = clone_with_track_id(det, tid)
                dets_fixed.append(det)

            # 2) dev risk_engine 그대로 호출
            metrics_map = engine.update(dets_fixed, (H, W), fd.frame_index, fd.fps)

            # 3) 사람 WARN “후처리 강제”: 조건 만족할 때만 WARN 남기기
            patched_levels: Dict[int, int] = {}
            for i, det in enumerate(dets_fixed):
                m = metrics_map.get(i)
                if m is None:
                    continue

                lvl = int(getattr(m, "risk_level", RISK_SAFE))
                cls_name = get_cls_name(det)

                # Person에 한해 WARN 허용조건을 강제
                if cls_name == "Person":
                    ok = strict_person_warn_gate(det, m, W, H, warn_pttc_s, border_margin_ratio)
                    # 로컬 연속 프레임 게이트까지 통과해야 WARN 유지
                    tid = get_track_id(det)
                    ok2 = person_warn_gate.step(tid, ok)
                    if lvl == RISK_WARN and not ok2:
                        lvl = RISK_CAUTION  # WARN -> CAUTION
                    # CAUTION도 원하면 더 강하게: approaching 아니면 SAFE로(옵션)
                    if not bool(getattr(m, "approaching", False)) and lvl >= RISK_CAUTION:
                        lvl = RISK_SAFE

                patched_levels[i] = lvl

            # 4) draw
            best_idx = None
            best_lvl = -1
            for i, lvl in patched_levels.items():
                if lvl > best_lvl:
                    best_lvl = lvl
                    best_idx = i

            for i, det in enumerate(dets_fixed):
                m = metrics_map.get(i)
                if m is None:
                    continue

                lvl = patched_levels.get(i, int(getattr(m, "risk_level", RISK_SAFE)))
                name = RISK_NAME.get(lvl, str(lvl))

                x1, y1, x2, y2 = map(int, get_xyxy(det))
                color = _color_for(lvl)
                thick = 4 if best_idx == i else 2
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thick)

                pttc_s = float(getattr(m, "pttc_s", 1e9))
                cr = float(getattr(m, "closing_rate", 0.0))
                inc = bool(getattr(m, "in_center", False))
                app = bool(getattr(m, "approaching", False))

                label = f"{get_cls_name(det)} id={get_track_id(det)} {name} pTTC={pttc_s:.1f}s cr={cr:.3f} inc={int(inc)} app={int(app)}"
                cv2.putText(frame, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)

            cv2.putText(frame, f"FPS: {fd.fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

            if args.show:
                cv2.imshow("Obstacle (dev engine + patch)", frame)
                if (cv2.waitKey(1) & 0xFF) == ord("q"):
                    cv2.destroyAllWindows()
                    return


if __name__ == "__main__":
    main()
