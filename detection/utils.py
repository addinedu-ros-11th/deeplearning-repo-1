"""
Utility functions for detection modules
"""

import cv2
import numpy as np
from typing import Tuple


def preprocess_frame(
    frame: np.ndarray, target_size: Tuple[int, int] = None
) -> np.ndarray:
    """
    프레임을 전처리합니다

    Args:
        frame: 입력 프레임
        target_size: 목표 크기 (width, height)

    Returns:
        전처리된 프레임
    """
    if target_size:
        frame = cv2.resize(frame, target_size)

    # 노이즈 제거
    frame = cv2.GaussianBlur(frame, (5, 5), 0)

    return frame


def calculate_iou(box1: Tuple, box2: Tuple) -> float:
    """
    두 바운딩 박스의 IoU를 계산합니다

    Args:
        box1: (x1, y1, x2, y2)
        box2: (x1, y1, x2, y2)

    Returns:
        IoU 값
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # 교집합 영역
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    if x2_i < x1_i or y2_i < y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)

    # 합집합 영역
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection

    if union == 0:
        return 0.0

    return intersection / union


def non_max_suppression(detections: list, iou_threshold: float = 0.5) -> list:
    """
    Non-Maximum Suppression을 수행합니다

    Args:
        detections: 감지 결과 리스트
        iou_threshold: IoU 임계값

    Returns:
        필터링된 감지 결과
    """
    if not detections:
        return []

    # 신뢰도 기준으로 정렬
    detections = sorted(detections, key=lambda x: x["confidence"], reverse=True)

    keep = []
    while detections:
        current = detections.pop(0)
        keep.append(current)

        # 현재 박스와 IoU가 높은 박스들 제거
        detections = [
            det
            for det in detections
            if calculate_iou(current["bbox"], det["bbox"]) < iou_threshold
        ]

    return keep
