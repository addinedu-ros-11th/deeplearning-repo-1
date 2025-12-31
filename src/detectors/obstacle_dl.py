from ultralytics import YOLO
import cv2
from common.config import config


class ObstacleDetector:
    def __init__(self, model_path=None):
        # YOLOv8/v11 모델 로드
        if model_path is None:
            model_path = (
                config.model.obstacle_detector.weights
                if config
                else "models/obstacle_detector/dummy.pt"
            )
        self.model = YOLO(model_path)
        # 위험 감지 임계값 (Confidence)
        self.threshold = config.model.obstacle_detector.confidence if config else 0.5

    def detect(self, frame):
        """
        이미지를 분석하여 장애물 유무와 위험도를 반환
        """
        try:
            results = self.model.predict(frame, conf=self.threshold, verbose=False)
        except Exception as e:
            print(f"[ObstacleDetector] Error in predict: {e}")
            return {"danger_level": 0.0, "objects": []}

        danger_level = 0.0
        detected_objects = []

        # 안전한 None 체크
        if results is None or len(results) == 0:
            return {"danger_level": 0.0, "objects": []}

        for result in results:
            if result.boxes is None or len(result.boxes) == 0:
                continue

            for box in result.boxes:
                # 클래스 정보 (0: person, 1: cart 등 가디언 설정에 따름)
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                # 바운딩 박스 크기를 통해 대략적인 위험도 계산 (화면 점유율 기반)
                x1, y1, x2, y2 = box.xyxy[0]
                box_area = (x2 - x1) * (y2 - y1)
                frame_area = frame.shape[0] * frame.shape[1]

                # 화면에서 객체가 차지하는 비율이 높을수록 가깝다고 판단
                occupancy = float(box_area / frame_area)
                if occupancy > danger_level:
                    danger_level = occupancy

                detected_objects.append(
                    {
                        "class": cls,
                        "confidence": conf,
                        "box": [int(x1), int(y1), int(x2), int(y2)],
                    }
                )

        return {"danger_level": danger_level, "objects": detected_objects}  # 0.0 ~ 1.0
