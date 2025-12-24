"""
Image utility functions
"""

import cv2
import numpy as np
from typing import Tuple
import base64


def resize_image(
    image: np.ndarray, width: int = None, height: int = None
) -> np.ndarray:
    """
    이미지 크기 조정

    Args:
        image: 입력 이미지
        width: 목표 너비
        height: 목표 높이

    Returns:
        크기 조정된 이미지
    """
    if width is None and height is None:
        return image

    h, w = image.shape[:2]

    if width is None:
        aspect_ratio = height / h
        width = int(w * aspect_ratio)
    elif height is None:
        aspect_ratio = width / w
        height = int(h * aspect_ratio)

    return cv2.resize(image, (width, height))


def crop_image(image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
    """
    이미지 자르기

    Args:
        image: 입력 이미지
        bbox: (x1, y1, x2, y2)

    Returns:
        잘린 이미지
    """
    x1, y1, x2, y2 = bbox
    return image[y1:y2, x1:x2]


def encode_image_to_base64(image: np.ndarray) -> str:
    """
    이미지를 Base64로 인코딩

    Args:
        image: 입력 이미지

    Returns:
        Base64 인코딩된 문자열
    """
    _, buffer = cv2.imencode(".jpg", image)
    return base64.b64encode(buffer).decode("utf-8")


def decode_base64_to_image(base64_str: str) -> np.ndarray:
    """
    Base64 문자열을 이미지로 디코딩

    Args:
        base64_str: Base64 인코딩된 문자열

    Returns:
        이미지
    """
    image_data = base64.b64decode(base64_str)
    nparr = np.frombuffer(image_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


def save_image(image: np.ndarray, filepath: str) -> bool:
    """
    이미지 저장

    Args:
        image: 저장할 이미지
        filepath: 저장 경로

    Returns:
        성공 여부
    """
    try:
        cv2.imwrite(filepath, image)
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False


def load_image(filepath: str) -> np.ndarray:
    """
    이미지 로드

    Args:
        filepath: 이미지 경로

    Returns:
        이미지
    """
    return cv2.imread(filepath)


def draw_text_with_background(
    image: np.ndarray,
    text: str,
    position: Tuple[int, int],
    font_scale: float = 0.6,
    thickness: int = 2,
    text_color: Tuple[int, int, int] = (255, 255, 255),
    bg_color: Tuple[int, int, int] = (0, 0, 0),
) -> np.ndarray:
    """
    배경이 있는 텍스트 그리기

    Args:
        image: 입력 이미지
        text: 텍스트
        position: 위치 (x, y)
        font_scale: 폰트 크기
        thickness: 두께
        text_color: 텍스트 색상
        bg_color: 배경 색상

    Returns:
        텍스트가 그려진 이미지
    """
    result = image.copy()
    x, y = position

    # 텍스트 크기 계산
    (text_width, text_height), baseline = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
    )

    # 배경 그리기
    cv2.rectangle(
        result,
        (x, y - text_height - baseline),
        (x + text_width, y + baseline),
        bg_color,
        -1,
    )

    # 텍스트 그리기
    cv2.putText(
        result,
        text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        text_color,
        thickness,
    )

    return result
