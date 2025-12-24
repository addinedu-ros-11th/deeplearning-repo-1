"""
Obstacle detection using YOLO models
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple
from config.config import Config
import time


class ObstacleDetector:
    """장애물 인식 클래스"""

    def __init__(self):
        self.config = Config()
        self.models = {}
        self.load_models()
        self.confidence_threshold = self.config.get(
            "yolo.obstacle.confidence_threshold", 0.7
        )

        # 장애물 추적을 위한 이전 위치 저장
        self.prev_positions = {}
        self.prev_time = time.time()

    def load_models(self):
        """YOLO 모델들을 로드합니다"""
        try:
            # 사람 감지 모델
            person_path = self.config.get("yolo.obstacle.person_model")
            self.models["person"] = YOLO(person_path)

            # 카트 감지 모델
            cart_path = self.config.get("yolo.obstacle.cart_model")
            self.models["cart"] = YOLO(cart_path)

            print("Obstacle detection models loaded successfully")
        except Exception as e:
            print(f"Error loading obstacle models: {e}")

    def detect_obstacles(self, frame: np.ndarray) -> List[Dict]:
        """
        프레임에서 장애물을 감지합니다

        Args:
            frame: 입력 이미지 프레임

        Returns:
            감지된 장애물 정보 리스트
            [{'type': str, 'confidence': float, 'bbox': tuple,
              'distance': float, 'direction': str, 'speed': float}]
        """
        detected_obstacles = []
        current_time = time.time()
        time_diff = current_time - self.prev_time

        for obstacle_type, model in self.models.items():
            try:
                results = model(frame, conf=self.confidence_threshold)

                for result in results:
                    boxes = result.boxes
                    for i, box in enumerate(boxes):
                        # Bounding box 좌표
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])

                        # 중심점 계산
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2

                        # 거리 추정 (바운딩 박스 크기 기반)
                        bbox_height = y2 - y1
                        distance = self._estimate_distance(bbox_height)

                        # 방향 계산
                        direction = self._calculate_direction(center_x, frame.shape[1])

                        # 속도 계산
                        speed = 0.0
                        obstacle_id = f"{obstacle_type}_{i}"
                        if obstacle_id in self.prev_positions and time_diff > 0:
                            prev_center = self.prev_positions[obstacle_id]
                            pixel_movement = np.sqrt(
                                (center_x - prev_center[0]) ** 2
                                + (center_y - prev_center[1]) ** 2
                            )
                            speed = self._estimate_speed(
                                pixel_movement, time_diff, distance
                            )

                        # 현재 위치 저장
                        self.prev_positions[obstacle_id] = (center_x, center_y)

                        # 경고 레벨 계산
                        warning_level = self._calculate_warning_level(distance, speed)

                        detected_obstacles.append(
                            {
                                "type": obstacle_type,
                                "confidence": confidence,
                                "bbox": (int(x1), int(y1), int(x2), int(y2)),
                                "center": (int(center_x), int(center_y)),
                                "distance": round(distance, 2),
                                "direction": direction,
                                "speed": round(speed, 2),
                                "warning_level": warning_level,
                                "class_id": class_id,
                            }
                        )
            except Exception as e:
                print(f"Error detecting {obstacle_type}: {e}")

        self.prev_time = current_time
        return detected_obstacles

    def _estimate_distance(self, bbox_height: float) -> float:
        """
        바운딩 박스 높이로 거리를 추정합니다
        (실제 구현 시 카메라 캘리브레이션 필요)

        Args:
            bbox_height: 바운딩 박스 높이

        Returns:
            추정 거리 (미터)
        """
        # 간단한 역비례 관계 (실제로는 더 정교한 계산 필요)
        if bbox_height > 0:
            return max(0.5, 100.0 / bbox_height)
        return 10.0

    def _calculate_direction(self, center_x: float, frame_width: int) -> str:
        """
        장애물의 방향을 계산합니다

        Args:
            center_x: 중심 x 좌표
            frame_width: 프레임 너비

        Returns:
            방향 문자열 (left, center, right)
        """
        relative_pos = center_x / frame_width

        if relative_pos < 0.35:
            return "left"
        elif relative_pos > 0.65:
            return "right"
        else:
            return "center"

    def _estimate_speed(
        self, pixel_movement: float, time_diff: float, distance: float
    ) -> float:
        """
        장애물의 속도를 추정합니다

        Args:
            pixel_movement: 픽셀 이동 거리
            time_diff: 시간 차이 (초)
            distance: 추정 거리 (미터)

        Returns:
            추정 속도 (m/s)
        """
        if time_diff > 0:
            # 픽셀 이동을 실제 거리로 변환 (간단한 근사)
            real_movement = pixel_movement * distance / 1000.0
            return real_movement / time_diff
        return 0.0

    def _calculate_warning_level(self, distance: float, speed: float) -> str:
        """
        경고 레벨을 계산합니다

        Args:
            distance: 거리 (미터)
            speed: 속도 (m/s)

        Returns:
            경고 레벨 (normal, warning, critical)
        """
        warning_distance = self.config.get("obstacle.warning_distance", 1.5)
        critical_distance = self.config.get("obstacle.critical_distance", 0.5)

        # 충돌 예상 시간 계산
        if speed > 0.1:
            time_to_collision = distance / speed
            collision_threshold = self.config.get(
                "obstacle.collision_time_threshold", 2.0
            )

            if time_to_collision < collision_threshold or distance < critical_distance:
                return "critical"

        if distance < warning_distance:
            return "warning"

        return "normal"

    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        감지된 장애물을 프레임에 그립니다

        Args:
            frame: 입력 이미지 프레임
            detections: 감지된 장애물 정보 리스트

        Returns:
            표시된 이미지 프레임
        """
        annotated_frame = frame.copy()

        for detection in detections:
            bbox = detection["bbox"]
            x1, y1, x2, y2 = bbox

            # 경고 레벨에 따른 색상
            color_map = {
                "normal": (0, 255, 0),  # 녹색
                "warning": (0, 165, 255),  # 주황색
                "critical": (0, 0, 255),  # 빨간색
            }
            color = color_map.get(detection["warning_level"], (0, 255, 0))

            # 바운딩 박스 그리기
            thickness = 3 if detection["warning_level"] == "critical" else 2
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)

            # 레이블 텍스트
            label = f"{detection['type']}"
            info = f"D:{detection['distance']}m S:{detection['speed']}m/s"
            direction = f"Dir:{detection['direction']}"

            # 텍스트 배경 및 텍스트
            y_offset = y1 - 10
            for text in [label, info, direction]:
                (text_width, text_height), _ = cv2.getTextSize(
                    text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                cv2.rectangle(
                    annotated_frame,
                    (x1, y_offset - text_height - 5),
                    (x1 + text_width, y_offset),
                    color,
                    -1,
                )
                cv2.putText(
                    annotated_frame,
                    text,
                    (x1, y_offset - 3),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )
                y_offset -= text_height + 5

        return annotated_frame
