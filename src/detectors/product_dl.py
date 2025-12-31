from ultralytics import YOLO
from common.config import config
import time
import numpy as np


class ProductRecognizer:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = (
                config.model.product_recognizer.weights
                if config
                else "models/product_recognizer/product_yolov8s.pt"
            )
        self.model = YOLO(model_path)
        self.threshold = config.model.product_recognizer.confidence if config else 0.7

        # Check if model is OBB (Oriented Bounding Box) or regular detection
        self.is_obb = self.model.task == "obb"
        print(
            f"[ProductRecognizer] Model type: {'OBB' if self.is_obb else 'Detection'}"
        )

        # 시간 기반 인식 시스템
        self.tracked_objects = (
            {}
        )  # {product_id: {"first_seen": time, "last_seen": time, "bbox": list}}
        self.last_added = {}  # {product_id: timestamp} - 쿨다운용
        self.cooldown_seconds = 3  # 같은 물건 3초 내 재인식 방지
        self.required_duration = 1.5  # 1.5초간 지속적으로 인식되어야 추가됨

    def recognize(self, frame):
        """
        프레임 내의 상품을 인식하여 DB 조회를 위한 ID 반환
        바운딩 박스 정보도 포함
        """
        try:
            results = self.model.predict(frame, conf=self.threshold, verbose=False)

            # 안전한 None 체크
            if results is None:
                return {"status": "none"}

            # OBB vs Detection 모델 처리
            if self.is_obb:
                if (
                    len(results) > 0
                    and results[0].obb is not None
                    and len(results[0].obb) > 0
                ):
                    # OBB 모델: obb 속성 사용
                    top_box = results[0].obb[0]
                    yolo_class = int(top_box.cls[0])
                    confidence = float(top_box.conf[0])

                    # OBB는 회전된 박스이므로 xyxyxyxy (8개 좌표) 형식
                    # 하지만 간단하게 하려면 xyxy 형식으로 변환
                    xyxyxyxy = top_box.xyxyxyxy[0].cpu().numpy()
                    x_coords = xyxyxyxy[::2]  # x 좌표들
                    y_coords = xyxyxyxy[1::2]  # y 좌표들
                    bbox = [
                        float(x_coords.min()),
                        float(y_coords.min()),
                        float(x_coords.max()),
                        float(y_coords.max()),
                    ]

                    product_id = yolo_class + 1
                    return {
                        "product_id": product_id,
                        "confidence": confidence,
                        "bbox": bbox,
                        "status": "detected",
                    }
            else:
                if (
                    len(results) > 0
                    and results[0].boxes is not None
                    and len(results[0].boxes) > 0
                ):
                    # 일반 Detection 모델: boxes 속성 사용
                    top_box = results[0].boxes[0]
                    yolo_class = int(top_box.cls[0])
                    product_id = yolo_class + 1
                    confidence = float(top_box.conf[0])
                    bbox = top_box.xyxy[0].cpu().numpy().tolist()

                    return {
                        "product_id": product_id,
                        "confidence": confidence,
                        "bbox": bbox,
                        "status": "detected",
                    }

        except Exception as e:
            print(f"[ProductRecognizer] Error in recognize: {e}")

        return {"status": "none"}

    def recognize_with_trigger(self, frame, current_time=None):
        """
        시간 기반 상품 인식 메서드

        동작 원리:
        1. 물체 감지 시작 → 추적 시작
        2. 1.5초간 지속적으로 인식되면 → "카트에 추가됨" 이벤트 발생
        3. 쿨다운: 같은 물건을 3초 내에 재인식하지 않음

        Args:
            frame: 입력 프레임
            current_time: 현재 시간 (None이면 자동 생성)

        Returns:
            dict: {
                "status": "added" | "tracking" | "none",
                "main_event": {...},  # 주요 이벤트 (added 또는 tracking)
                "all_detections": [...]  # 모든 감지된 물체들 (바운딩 박스 표시용)
            }
        """
        if current_time is None:
            current_time = time.time()

        try:
            results = self.model.predict(frame, conf=self.threshold, verbose=False)
        except Exception as e:
            print(f"[ProductRecognizer] Error in predict: {e}")
            return {"status": "none", "all_detections": []}

        # 현재 프레임에서 감지된 모든 물체들
        all_detections = []
        main_event = None

        # 안전한 None 체크
        if results is None or len(results) == 0:
            return {"status": "none", "all_detections": []}

        # OBB vs Detection 모델 처리
        boxes_data = []
        if self.is_obb:
            if results[0].obb is not None and len(results[0].obb) > 0:
                for obb_box in results[0].obb:
                    # OBB를 일반 bbox로 변환
                    xyxyxyxy = obb_box.xyxyxyxy[0].cpu().numpy()
                    x_coords = xyxyxyxy[::2]
                    y_coords = xyxyxyxy[1::2]
                    bbox = np.array(
                        [x_coords.min(), y_coords.min(), x_coords.max(), y_coords.max()]
                    )

                    boxes_data.append(
                        {
                            "bbox": bbox,
                            "cls": int(obb_box.cls[0]),
                            "conf": float(obb_box.conf[0]),
                        }
                    )
        else:
            if results[0].boxes is not None and len(results[0].boxes) > 0:
                for box in results[0].boxes:
                    boxes_data.append(
                        {
                            "bbox": box.xyxy[0].cpu().numpy(),
                            "cls": int(box.cls[0]),
                            "conf": float(box.conf[0]),
                        }
                    )

        if len(boxes_data) > 0:
            for box_data in boxes_data:
                product_id = box_data["cls"] + 1
                bbox = box_data["bbox"]
                center_y = (bbox[1] + bbox[3]) / 2
                confidence = box_data["conf"]

                # 모든 물체 정보 수집 (바운딩 박스 표시용)
                detection_info = {
                    "product_id": product_id,
                    "confidence": confidence,
                    "bbox": bbox.tolist(),
                    "center_y": center_y,
                }

                # 쿨다운 체크 - 최근에 추가한 물건
                if product_id in self.last_added:
                    time_since_added = current_time - self.last_added[product_id]
                    if time_since_added < self.cooldown_seconds:
                        detection_info["state"] = "cooldown"
                        detection_info["cooldown_remaining"] = (
                            self.cooldown_seconds - time_since_added
                        )
                        all_detections.append(detection_info)
                        continue

                # 추적 상태 업데이트
                if product_id not in self.tracked_objects:
                    # 새로 발견된 물체 - 추적 시작
                    self.tracked_objects[product_id] = {
                        "first_seen": current_time,
                        "last_seen": current_time,
                        "bbox": bbox.tolist(),
                    }

                    detection_info["state"] = "tracking"
                    detection_info["duration"] = 0.0
                    all_detections.append(detection_info)

                    if main_event is None:
                        main_event = {
                            "product_id": product_id,
                            "confidence": confidence,
                            "bbox": bbox.tolist(),
                            "status": "tracking",
                            "duration": 0.0,
                        }
                else:
                    # 이미 추적 중인 물체
                    obj = self.tracked_objects[product_id]
                    obj["last_seen"] = current_time
                    obj["bbox"] = bbox.tolist()

                    duration = current_time - obj["first_seen"]

                    # 시간 기반 트리거 체크
                    if duration >= self.required_duration:
                        # 🎉 카트에 추가됨!
                        self.last_added[product_id] = current_time
                        del self.tracked_objects[product_id]

                        detection_info["state"] = "added"
                        detection_info["duration"] = duration
                        all_detections.append(detection_info)

                        main_event = {
                            "product_id": product_id,
                            "confidence": confidence,
                            "bbox": bbox.tolist(),
                            "status": "added",
                            "trigger": "duration_reached",
                            "duration": duration,
                        }
                    else:
                        # 아직 시간이 안됨 - 계속 추적
                        detection_info["state"] = "tracking"
                        detection_info["duration"] = duration
                        detection_info["remaining"] = self.required_duration - duration
                        all_detections.append(detection_info)

                        if main_event is None:
                            main_event = {
                                "product_id": product_id,
                                "confidence": confidence,
                                "bbox": bbox.tolist(),
                                "status": "tracking",
                                "duration": duration,
                                "remaining": self.required_duration - duration,
                            }

        # 오래된 추적 정보 정리 (2초 이상 보이지 않으면 제거)
        lost_ids = []
        for pid, data in self.tracked_objects.items():
            if current_time - data.get("last_seen", current_time) > 2.0:
                lost_ids.append(pid)

        for pid in lost_ids:
            del self.tracked_objects[pid]

        # 쿨다운 정리 (쿨다운 시간이 지난 항목 제거)
        cooldown_cleanup = []
        for pid, added_time in self.last_added.items():
            if current_time - added_time > self.cooldown_seconds:
                cooldown_cleanup.append(pid)

        for pid in cooldown_cleanup:
            del self.last_added[pid]

        # 결과 반환
        if main_event and main_event["status"] == "added":
            return {
                "status": "added",
                "main_event": main_event,
                "all_detections": all_detections,
            }
        elif main_event:
            return {
                "status": "tracking",
                "main_event": main_event,
                "all_detections": all_detections,
            }
        else:
            return {"status": "none", "all_detections": all_detections}

    def get_debug_zones(self, frame_shape):
        """
        디버깅용: 추적 정보 반환

        Returns:
            dict: {
                "tracked_count": int,
                "cooldown_count": int,
                "required_duration": float
            }
        """
        return {
            "tracked_count": len(self.tracked_objects),
            "cooldown_count": len(self.last_added),
            "required_duration": self.required_duration,
        }

    def reset_tracking(self):
        """추적 상태 초기화"""
        self.tracked_objects.clear()
        self.last_added.clear()
