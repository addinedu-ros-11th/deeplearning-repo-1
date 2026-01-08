from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Union

import cv2

from detector import YoloTrackerDetector
from logger import EventLogger, WarnEvent
from risk_engine import RiskEngine, RiskEngineConfig, RISK_WARN


def _load_config(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    text = p.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except Exception:
        return json.loads(text)


def _parse_source(src: str) -> Union[int, str]:
    return int(src) if src.isdigit() else src


def _color_for_risk(risk_name: str):
    # BGR
    if risk_name == "WARN":
        return (0, 0, 255)
    if risk_name == "CAUTION":
        return (0, 255, 255)
    return (0, 255, 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, default="config.yaml")
    ap.add_argument("--source", type=str, default="0")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--save_video", action="store_true")
    ap.add_argument("--out_dir", type=str, default="")
    args = ap.parse_args()

    cfg = _load_config(args.config)

    weights = cfg["models"]["weights"]
    det_conf = float(cfg["inference"].get("conf", 0.35))
    det_iou = float(cfg["inference"].get("iou", 0.5))
    imgsz = int(cfg["inference"].get("imgsz", 640))
    device = cfg["inference"].get("device", "0")
    tracker = cfg.get("tracking", {}).get("tracker", "bytetrack.yaml")
    persist = bool(cfg.get("tracking", {}).get("persist", True))

    # output dir
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        ts = EventLogger.now_iso().replace(":", "-")
        out_dir = Path(cfg.get("output", {}).get("base_dir", "runs_obstacle")) / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    logger = EventLogger(
        out_dir=str(out_dir),
        csv_name=cfg.get("output", {}).get("csv_name", "events.csv"),
        save_snapshots=bool(cfg.get("output", {}).get("save_snapshots", True)),
    )

    # risk config
    r = cfg.get("risk", {})
    risk_cfg = RiskEngineConfig(
        center_band_ratio=float(r.get("center_band_ratio", 0.45)),
        near_center_band_ratio=float(r.get("near_center_band_ratio", 0.65)),
        ema_alpha=float(r.get("ema_alpha", 0.35)),
        closing_rate_min=float(r.get("closing_rate_min", 0.02)),
        streak_warn=int(r.get("streak_warn", 8)),
        streak_caution=int(r.get("streak_caution", 4)),
        pttc_warn_s=float(r.get("pttc_warn_s", 2.0)),
        pttc_caution_s=float(r.get("pttc_caution_s", 4.0)),
        mega_close_boxh_ratio=float(r.get("mega_close_boxh_ratio", 0.55)),
        mega_close_area_ratio=float(r.get("mega_close_area_ratio", 0.35)),
        hysteresis_frames=int(r.get("hysteresis_frames", 10)),
        stale_frames=int(r.get("stale_frames", 30)),
        class_weights=dict(r.get("class_weights", {"Person": 1.0, "Cart": 0.8})),
        center_bonus=float(r.get("center_bonus", 0.2)),
        approach_bonus=float(r.get("approach_bonus", 0.2)),
    )
    risk_engine = RiskEngine(risk_cfg)

    detector = YoloTrackerDetector(
        weights=weights,
        tracker=tracker,
        conf=det_conf,
        iou=det_iou,
        imgsz=imgsz,
        device=device,
        persist=persist,
        verbose=bool(cfg.get("inference", {}).get("verbose", False)),
    )

    source = _parse_source(args.source)

    writer = None
    video_path = None
    last_warn_track_ids = set()

    try:
        for fd in detector.stream(source):
            frame = fd.frame_bgr.copy()
            H, W = frame.shape[:2]

            metrics_map = risk_engine.update(fd.detections, (H, W), fd.frame_index, fd.fps)

            # BEST by score
            best_idx = None
            best_score = -1e18
            for idx, m in metrics_map.items():
                if m.score > best_score:
                    best_score = m.score
                    best_idx = idx

            for i, det in enumerate(fd.detections):
                m = metrics_map.get(i)
                if m is None:
                    continue

                x1, y1, x2, y2 = map(int, det.xyxy)
                color = _color_for_risk(m.risk_name)
                thickness = 4 if best_idx == i else 2

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

                label = f"{det.cls_name} id={det.track_id} {m.risk_name} pTTC={m.pttc_s:.1f}s"
                cv2.putText(frame, label, (x1, max(20, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

                # WARN 상승 순간만 로그
                if m.risk_level == RISK_WARN and int(det.track_id) not in last_warn_track_ids:
                    ev = WarnEvent(
                        timestamp=logger.now_iso(),
                        frame_index=fd.frame_index,
                        track_id=int(det.track_id),
                        cls_name=det.cls_name,
                        score=float(m.score),
                        pttc_s=float(m.pttc_s),
                        dist_proxy=float(m.dist_proxy),
                        closing_rate=float(m.closing_rate),
                        xyxy=det.xyxy,
                    )
                    logger.log_warn(ev, frame)
                    last_warn_track_ids.add(int(det.track_id))

                if m.risk_level != RISK_WARN and int(det.track_id) in last_warn_track_ids:
                    last_warn_track_ids.remove(int(det.track_id))

            # 상단 요약
            if best_idx is not None:
                best_det = fd.detections[best_idx]
                best_m = metrics_map[best_idx]
                summary = f"BEST: {best_m.risk_name} | {best_det.cls_name} id={best_det.track_id} | pTTC={best_m.pttc_s:.1f}s | fps={fd.fps:.1f}"
            else:
                summary = f"No detections | fps={fd.fps:.1f}"
            cv2.putText(frame, summary, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

            # 비디오 저장(옵션)
            if args.save_video and writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                video_path = str(out_dir / "annotated.mp4")
                writer = cv2.VideoWriter(video_path, fourcc, max(10.0, fd.fps), (W, H))

            if writer is not None:
                writer.write(frame)

            if args.show:
                cv2.imshow("Obstacle Detector (v2)", frame)
                if (cv2.waitKey(1) & 0xFF) == ord("q"):
                    break

    finally:
        if writer is not None:
            writer.release()
        logger.close()
        if args.show:
            cv2.destroyAllWindows()

    print(f"✅ done. outputs: {out_dir}")
    if video_path:
        print(f"🎬 video: {video_path}")


if __name__ == "__main__":
    main()
