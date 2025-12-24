"""
Quality inspection module for product damage detection
"""

import cv2
import numpy as np
from typing import Dict, Tuple
from config.config import Config


class QualityInspector:
    """상품 품질 검사 클래스"""

    def __init__(self):
        self.config = Config()
        self.damage_threshold = self.config.get("quality.damage_threshold", 0.3)

    def inspect_quality(
        self, frame: np.ndarray, bbox: Tuple[int, int, int, int]
    ) -> Dict:
        """
        상품의 품질을 검사합니다

        Args:
            frame: 입력 이미지 프레임
            bbox: 상품의 바운딩 박스 (x1, y1, x2, y2)

        Returns:
            품질 검사 결과
            {'is_damaged': bool, 'damage_score': float, 'defects': list}
        """
        x1, y1, x2, y2 = bbox

        # 상품 영역 추출
        product_roi = frame[y1:y2, x1:x2]

        if product_roi.size == 0:
            return {"is_damaged": False, "damage_score": 0.0, "defects": []}

        # 품질 검사 수행
        defects = []
        damage_score = 0.0

        # 1. 기하학적 변형 감지
        geometry_score = self._check_geometric_deformation(product_roi)
        if geometry_score > self.damage_threshold:
            defects.append("geometric_deformation")
            damage_score = max(damage_score, geometry_score)

        # 2. 질감 이상 감지
        texture_score = self._check_texture_abnormality(product_roi)
        if texture_score > self.damage_threshold:
            defects.append("texture_abnormality")
            damage_score = max(damage_score, texture_score)

        # 3. 색상 이상 감지
        color_score = self._check_color_abnormality(product_roi)
        if color_score > self.damage_threshold:
            defects.append("color_abnormality")
            damage_score = max(damage_score, color_score)

        is_damaged = damage_score > self.damage_threshold

        return {
            "is_damaged": is_damaged,
            "damage_score": round(damage_score, 3),
            "defects": defects,
        }

    def _check_geometric_deformation(self, roi: np.ndarray) -> float:
        """
        기하학적 변형을 검사합니다

        Args:
            roi: 상품 영역 이미지

        Returns:
            변형 점수 (0.0 ~ 1.0)
        """
        try:
            # 그레이스케일 변환
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # 엣지 검출
            edges = cv2.Canny(gray, 50, 150)

            # 윤곽선 검출
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                return 0.0

            # 가장 큰 윤곽선 선택
            largest_contour = max(contours, key=cv2.contourArea)

            # 윤곽선의 볼록 결함 검사
            hull = cv2.convexHull(largest_contour, returnPoints=False)

            if len(largest_contour) > 3 and len(hull) > 3:
                defects = cv2.convexityDefects(largest_contour, hull)

                if defects is not None:
                    # 결함의 깊이 계산
                    max_depth = 0
                    for i in range(defects.shape[0]):
                        s, e, f, d = defects[i, 0]
                        depth = d / 256.0
                        max_depth = max(max_depth, depth)

                    # 정규화 (임의의 기준값 50 사용)
                    return min(1.0, max_depth / 50.0)

            return 0.0
        except Exception as e:
            print(f"Error in geometric deformation check: {e}")
            return 0.0

    def _check_texture_abnormality(self, roi: np.ndarray) -> float:
        """
        질감 이상을 검사합니다

        Args:
            roi: 상품 영역 이미지

        Returns:
            이상 점수 (0.0 ~ 1.0)
        """
        try:
            # 그레이스케일 변환
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

            # 라플라시안 필터로 텍스처 변화 감지
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()

            # 텍스처 분산이 너무 높거나 낮으면 이상으로 판단
            # 정규 범위를 벗어난 정도를 점수화
            if variance < 50:  # 너무 매끄러움 (흐릿함)
                return min(1.0, (50 - variance) / 50)
            elif variance > 500:  # 너무 거침 (손상)
                return min(1.0, (variance - 500) / 500)

            return 0.0
        except Exception as e:
            print(f"Error in texture abnormality check: {e}")
            return 0.0

    def _check_color_abnormality(self, roi: np.ndarray) -> float:
        """
        색상 이상을 검사합니다

        Args:
            roi: 상품 영역 이미지

        Returns:
            이상 점수 (0.0 ~ 1.0)
        """
        try:
            # HSV 색공간으로 변환
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            # 색상 히스토그램 계산
            h_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
            s_hist = cv2.calcHist([hsv], [1], None, [256], [0, 256])
            v_hist = cv2.calcHist([hsv], [2], None, [256], [0, 256])

            # 히스토그램 정규화
            h_hist = h_hist / h_hist.sum()
            s_hist = s_hist / s_hist.sum()
            v_hist = v_hist / v_hist.sum()

            # 색상 분포의 균일성 검사 (엔트로피 계산)
            h_entropy = -np.sum(h_hist * np.log2(h_hist + 1e-10))

            # 채도가 너무 낮으면 (변색 가능성)
            s_mean = np.mean(hsv[:, :, 1])
            if s_mean < 50:
                return min(1.0, (50 - s_mean) / 50)

            # 명도 분산이 너무 크면 (불균일한 손상)
            v_std = np.std(hsv[:, :, 2])
            if v_std > 60:
                return min(1.0, (v_std - 60) / 100)

            return 0.0
        except Exception as e:
            print(f"Error in color abnormality check: {e}")
            return 0.0

    def draw_quality_info(
        self, frame: np.ndarray, bbox: Tuple[int, int, int, int], quality_result: Dict
    ) -> np.ndarray:
        """
        품질 검사 결과를 프레임에 표시합니다

        Args:
            frame: 입력 이미지 프레임
            bbox: 상품의 바운딩 박스
            quality_result: 품질 검사 결과

        Returns:
            표시된 이미지 프레임
        """
        annotated_frame = frame.copy()
        x1, y1, x2, y2 = bbox

        if quality_result["is_damaged"]:
            # 손상된 경우 빨간색 표시
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)

            label = f"DAMAGED ({quality_result['damage_score']:.2f})"
            cv2.putText(
                annotated_frame,
                label,
                (x1, y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )
        else:
            # 정상인 경우 녹색 표시
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            label = "OK"
            cv2.putText(
                annotated_frame,
                label,
                (x1, y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

        return annotated_frame
