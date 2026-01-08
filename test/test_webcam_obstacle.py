from __future__ import annotations
import argparse
import yaml
from pathlib import Path
import cv2

# ✅ 정식 경로(src)에서 모듈 로드
from src.detectors.obstacle_tracker import YoloTrackerDetector
from src.detectors.risk_engine import RiskEngine, RiskEngineConfig, RISK_WARN
from src.detectors.obstacle_logger import EventLogger, WarnEvent

def _color(nm):
    return (0,0,255) if nm=="WARN" else (0,255,255) if nm=="CAUTION" else (0,255,0)

def main():
    ap = argparse.ArgumentParser()
    # ✅ 기본 설정 파일 경로 수정 (configs/...)
    ap.add_argument("--config", default="configs/model_config.yaml")
    ap.add_argument("--source", default="0")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())

    # Logger
    ts = EventLogger.now_iso().replace(":", "-")
    out_dir = Path(cfg["output"]["base_dir"]) / ts
    logger = EventLogger(str(out_dir), cfg["output"]["csv_name"], cfg["output"]["save_snapshots"])

    # Engine & Detector
    engine = RiskEngine(RiskEngineConfig(**cfg["risk"]))
    detector = YoloTrackerDetector(weights=cfg["models"]["weights"], **cfg.get("tracking",{}), **cfg.get("inference",{}))

    src = int(args.source) if args.source.isdigit() else args.source
    last_warn = set()

    try:
        for fd in detector.stream(src):
            frame = fd.frame_bgr.copy()
            H, W = frame.shape[:2]
            metrics = engine.update(fd.detections, (H, W), fd.frame_index, fd.fps)

            best_idx = max(metrics, key=lambda i: metrics[i].score) if metrics else None

            for i, det in enumerate(fd.detections):
                if i not in metrics: continue
                m = metrics[i]
                color = _color(m.risk_name)
                x1,y1,x2,y2 = map(int, det.xyxy)
                cv2.rectangle(frame, (x1,y1), (x2,y2), color, 4 if i==best_idx else 2)
                cv2.putText(frame, f"{det.cls_name} {m.risk_name} pTTC={m.pttc_s:.1f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                # Logging
                tid = int(det.track_id)
                if m.risk_level == RISK_WARN and tid not in last_warn:
                    logger.log_warn(WarnEvent(EventLogger.now_iso(), fd.frame_index, tid, det.cls_name, m.score, m.pttc_s, m.dist_proxy, m.closing_rate, det.xyxy), frame)
                    last_warn.add(tid)
                elif m.risk_level != RISK_WARN and tid in last_warn:
                    last_warn.remove(tid)

            if args.show:
                cv2.imshow("Obstacle Dev", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): break
    finally:
        logger.close()
        cv2.destroyAllWindows()
        print(f"Done. Logs at {out_dir}")

if __name__ == "__main__":
    main()
