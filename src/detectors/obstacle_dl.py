# src/detectors/obstacle_dl.py
import time
from typing import Any, Dict, List, Optional

from ultralytics import YOLO

from common.config import config
from common.protocols import DangerLevel

from detectors.obstacle_risk_engine import ObstacleRiskEngine, RiskParams


class ObstacleDetector:
    """
    Pose 기반 사람(Person) 장애물 인식 + 위험도(DangerLevel) 산출

    반환:
      {
        "danger_level": int (0/1/2),  # DangerLevel.NORMAL/CAUTION/CRITICAL
        "objects": [...],             # risk engine meta 포함
        "best": {...} or None
      }

    주의:
    - 기존 코드가 float(0~1)로 danger_level을 주던 것과 달리,
      이 버전은 protocols.DangerLevel에 맞춰 0/1/2 정수로 반환.
    - ai_server.py가 float를 기대한다면, 아래 _danger_to_float 옵션으로 쉽게 바꿀 수 있음.
    """

    def __init__(self, model_path: Optional[str] = None):
        # config 기반 weights 사용 (없으면 pose 기본)
        if model_path is None:
            model_path = (
                config.model.obstacle_detector.weights
                if config
                else "yolo11n-pose.pt"
            )

        self.model = YOLO(model_path)

        # confidence threshold (config 우선)
        self.threshold = config.model.obstacle_detector.confidence if config else 0.35

        # tracker/persist (없으면 기본)
        try:
            self.tracker = config.model.obstacle_detector.tracker
        except Exception:
            self.tracker = "bytetrack.yaml"

        try:
            self.persist = bool(config.model.obstacle_detector.persist)
        except Exception:
            self.persist = True

        # pose feet 보정 옵션(없으면 True)
        try:
            self.use_pose_feet = bool(config.model.obstacle_detector.use_pose_feet)
        except Exception:
            self.use_pose_feet = True

        try:
            self.kpt_conf_thr = float(config.model.obstacle_detector.kpt_conf_thr)
        except Exception:
            self.kpt_conf_thr = 0.30

        self.risk = ObstacleRiskEngine(RiskParams())

    # SAFE/CAUTION/WARN -> DangerLevel int(0/1/2)
    @staticmethod
    def _risk_to_danger_level(risk: str) -> int:
        if risk == "WARN":
            return int(DangerLevel.CRITICAL)
        if risk == "CAUTION":
            return int(DangerLevel.CAUTION)
        return int(DangerLevel.NORMAL)

    # (필요 시) DangerLevel int -> 0~1 float로 변환 (기존 engine/DB가 float를 기대하면 사용)
    @staticmethod
    def _danger_to_float(dl: int) -> float:
        # NORMAL=0.0, CAUTION=0.5, CRITICAL=1.0 같은 식으로 매핑
        if dl >= int(DangerLevel.CRITICAL):
            return 1.0
        if dl >= int(DangerLevel.CAUTION):
            return 0.5
        return 0.0

    def _extract_feet_y(self, kpts_xy, kpts_conf) -> Optional[float]:
        """
        COCO keypoints index:
        15=left_ankle, 16=right_ankle
        """
        if kpts_xy is None or kpts_conf is None:
            return None

        try:
            la_y = float(kpts_xy[15][1])
            ra_y = float(kpts_xy[16][1])
            la_c = float(kpts_conf[15])
            ra_c = float(kpts_conf[16])
        except Exception:
            return None

        ys = []
        if la_c >= self.kpt_conf_thr:
            ys.append(la_y)
        if ra_c >= self.kpt_conf_thr:
            ys.append(ra_y)
        return max(ys) if ys else None

    def detect(self, frame) -> Dict[str, Any]:
        """
        frame 1장을 입력으로 받아 person track -> risk -> danger_level 계산.
        """
        now_t = time.time()
        H, W = frame.shape[:2]

        # pose/detect 모두 boxes 제공. track 사용 시도, 실패하면 predict로 fallback.
        try:
            result = self.model.track(
                frame,
                persist=self.persist,
                tracker=self.tracker,
                conf=self.threshold,
                verbose=False,
                classes=[0],  # person
            )[0]
        except Exception:
            result = self.model.predict(frame, conf=self.threshold, verbose=False)[0]

        dets: List[Dict[str, Any]] = []

        if result.boxes is not None and len(result.boxes) > 0:
            ids = getattr(result.boxes, "id", None)
            has_cls = hasattr(result.boxes, "cls") and (result.boxes.cls is not None)

            # pose keypoints (있으면)
            kpts_xy_all = None
            kpts_conf_all = None
            if self.use_pose_feet and hasattr(result, "keypoints") and (result.keypoints is not None):
                try:
                    kpts_xy_all = result.keypoints.xy
                    kpts_conf_all = result.keypoints.conf
                except Exception:
                    kpts_xy_all = None
                    kpts_conf_all = None

            for i in range(len(result.boxes)):
                # predict fallback에서 classes 필터가 안 먹을 수 있으므로 한번 더 체크
                if has_cls:
                    cls = int(result.boxes.cls[i].item())
                    if cls != 0:
                        continue

                x1, y1, x2, y2 = map(int, result.boxes.xyxy[i].tolist())
                tid = int(ids[i].item()) if ids is not None else -1
                conf = float(result.boxes.conf[i].item()) if result.boxes.conf is not None else 1.0

                # feet-y로 y2 보정(바닥접점 추정)
                y2_adj = y2
                if self.use_pose_feet and (kpts_xy_all is not None) and (kpts_conf_all is not None):
                    try:
                        feet_y = self._extract_feet_y(kpts_xy_all[i], kpts_conf_all[i])
                        if feet_y is not None:
                            fy = int(max(y1 + 2, min(feet_y, H - 1)))
                            y2_adj = fy
                    except Exception:
                        pass

                dets.append({"track_id": tid, "xyxy": (x1, y1, x2, y2_adj), "conf": conf})

        out = self.risk.update_many(dets, now_t, H, W)
        best = out.get("best")

        danger_level = int(DangerLevel.NORMAL)
        if best is not None:
            danger_level = self._risk_to_danger_level(best["risk"])

        # 만약 시스템이 float(0~1)을 기대하면 아래 주석 해제해서 바꿀 수 있음:
        # danger_level = self._danger_to_float(danger_level)

        return {
            "danger_level": danger_level,
            "objects": out.get("objects", []),
            "best": best,
        }
