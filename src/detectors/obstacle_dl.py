"""
Advanced Obstacle Detection with Tracking and Risk Assessment
Integrated obstacle_v2 algorithm with original system compatibility
"""

import numpy as np
from common.config import config
from detectors.obstacle_tracker import YoloTrackerDetector
from detectors.risk_engine import (
    RiskEngine,
    RiskEngineConfig,
    RISK_SAFE,
    RISK_CAUTION,
    RISK_WARN,
)


class ObstacleDetector:
    """
    고급 장애물 감지기 - Track ID 기반 추적 및 위험도 평가
    - YOLO Tracking으로 객체 추적
    - RiskEngine으로 SAFE/CAUTION/WARN 판정
    - 기존 시스템과 호환되는 인터페이스 유지
    """

    def __init__(self, model_path=None):
        # 모델 경로 설정
        if model_path is None:
            model_path = (
                config.model.obstacle_detector.weights
                if config
                else "models/obstacle_detector/dummy.pt"
            )

        # 설정 로드
        conf_threshold = config.model.obstacle_detector.confidence if config else 0.35
        iou_threshold = (
            getattr(config.model.obstacle_detector, "iou_threshold", 0.5)
            if config
            else 0.5
        )

        # YOLO Tracker 초기화
        self.tracker = YoloTrackerDetector(
            weights=model_path,
            tracker="bytetrack.yaml",
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=640,
            device="0",
            persist=True,
            verbose=False,
        )

        # Risk Engine 설정
        risk_cfg = RiskEngineConfig()
        if config and hasattr(config.model.obstacle_detector, "risk"):
            risk_params = config.model.obstacle_detector.risk
            if isinstance(risk_params, dict):
                for key, value in risk_params.items():
                    if hasattr(risk_cfg, key):
                        setattr(risk_cfg, key, value)

        self.risk_engine = RiskEngine(risk_cfg)
        self.frame_index = 0
        self.last_fps = 30.0  # 기본 FPS

    def detect(self, frame):
        """
        이미지를 분석하여 장애물 유무와 위험도를 반환

        Returns:
            dict: {
                "level": int (0=SAFE, 1=CAUTION, 2=WARN),
                "danger_level": float (0.0-1.0, 하위 호환),
                "objects": list,
                "highest_risk_object": dict (가장 위험한 객체 정보),
                "metrics": dict (상세 위험도 메트릭)
            }
        """
        try:
            # YOLO Tracking 수행
            frame_detections = self.tracker.detect_single_frame(frame, self.frame_index)

            if not frame_detections.detections:
                return {
                    "level": 0,
                    "danger_level": 0.0,
                    "objects": [],
                }

            # Risk Engine으로 위험도 평가
            H, W = frame.shape[:2]
            risk_metrics = self.risk_engine.update(
                detections=frame_detections.detections,
                frame_shape_hw=(H, W),
                frame_index=self.frame_index,
                fps=self.last_fps,
            )

            # 결과 변환
            detected_objects = []
            max_risk_level = RISK_SAFE
            max_risk_score = 0.0
            highest_risk_obj = None

            for idx, det in enumerate(frame_detections.detections):
                metrics = risk_metrics.get(idx)
                if metrics is None:
                    continue

                x1, y1, x2, y2 = det.xyxy
                obj_info = {
                    "track_id": int(det.track_id),
                    "class": det.cls_id,
                    "class_name": det.cls_name,
                    "confidence": float(det.conf),
                    "box": [int(x1), int(y1), int(x2), int(y2)],
                    "risk_level": metrics.risk_level,
                    "risk_name": metrics.risk_name,
                    "score": metrics.score,
                    "pttc_s": metrics.pttc_s,
                    "in_center": metrics.in_center,
                    "approaching": metrics.approaching,
                }
                detected_objects.append(obj_info)

                # 최고 위험 객체 추적
                if metrics.risk_level > max_risk_level or (
                    metrics.risk_level == max_risk_level
                    and metrics.score > max_risk_score
                ):
                    max_risk_level = metrics.risk_level
                    max_risk_score = metrics.score
                    highest_risk_obj = obj_info

            # 하위 호환을 위한 danger_level 계산 (0.0-1.0)
            # SAFE=0 -> 0.0, CAUTION=1 -> 0.5, WARN=2 -> 1.0
            danger_level = max_risk_level / 2.0

            self.frame_index += 1

            return {
                "level": int(max_risk_level),  # 0=SAFE, 1=CAUTION, 2=WARN
                "danger_level": float(danger_level),  # 하위 호환용 (0.0-1.0)
                "objects": detected_objects,
                "highest_risk_object": highest_risk_obj,
                "object_type": (
                    highest_risk_obj["class_name"] if highest_risk_obj else "unknown"
                ),
                "distance": int(1000 * (1.0 - danger_level)),  # 근사치 (mm)
                "speed": 0,  # TODO: 추후 속도 계산 추가 가능
                "direction": "front",  # 기본값
            }

        except Exception as e:
            print(f"[ObstacleDetector] Error in detect: {e}")
            import traceback

            traceback.print_exc()
            return {
                "level": 0,
                "danger_level": 0.0,
                "objects": [],
            }
