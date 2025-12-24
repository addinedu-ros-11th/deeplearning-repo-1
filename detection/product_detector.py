"""
Product detection using YOLO models
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple
from config.config import Config


class ProductDetector:
    """상품 인식 클래스"""

    def __init__(self):
        self.config = Config()
        self.models = {}
        self.use_unified = self.config.get('yolo.product.use_unified', True)
        self.class_to_category = self.config.get('yolo.product.class_to_category', {})
        self.load_models()
        self.confidence_threshold = self.config.get(
            "yolo.product.confidence_threshold", 0.6
        )

    def load_models(self):
        """YOLO 모델들을 로드합니다"""
        try:
            if self.use_unified:
                # 방식 1 (권장): 통합 모델 사용
                unified_path = self.config.get('yolo.product.unified_model')
                self.models['unified'] = YOLO(unified_path)
                print(f"✓ Product detection unified model loaded: {unified_path}")
            else:
                # 방식 2: 카테고리별 모델 사용
                # 아이스크림 모델
                icecream_path = self.config.get("yolo.product.icecream_model")
                self.models["icecream"] = YOLO(icecream_path)

                # 과자 모델
                snack_path = self.config.get("yolo.product.snack_model")
                self.models["snack"] = YOLO(snack_path)

                # 라면 모델
                ramen_path = self.config.get("yolo.product.ramen_model")
                self.models["ramen"] = YOLO(ramen_path)

                print("✓ Product detection models loaded (category-based)")
        except Exception as e:
            print(f"✗ Error loading product models: {e}")

    def detect_products(self, frame: np.ndarray) -> List[Dict]:
        """
        프레임에서 상품을 감지합니다

        Args:
            frame: 입력 이미지 프레임

        Returns:
            감지된 상품 정보 리스트
            [{'category': str, 'name': str, 'confidence': float, 'bbox': tuple}]
        """
        if self.use_unified:
            # 방식 1: 통합 모델 사용 (1번 inference)
            return self._detect_with_unified_model(frame)
        else:
            # 방식 2: 카테고리별 모델 사용 (3번 inference)
            return self._detect_with_category_models(frame)

    def _detect_with_unified_model(self, frame: np.ndarray) -> List[Dict]:
        """통합 모델로 상품을 감지합니다 (권장)"""
        detected_products = []

        try:
            model = self.models['unified']
            results = model(frame, conf=self.confidence_threshold)

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Bounding box 좌표
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])

                    # 클래스 이름 가져오기
                    class_name = model.names[class_id]

                    # 클래스 ID로 카테고리 매핑
                    category = self.class_to_category.get(str(class_id), 'unknown')

                    detected_products.append({
                        'category': category,
                        'name': class_name,
                        'confidence': confidence,
                        'bbox': (int(x1), int(y1), int(x2), int(y2)),
                        'class_id': class_id
                    })
        except Exception as e:
            print(f"Error detecting with unified model: {e}")

        return detected_products

    def _detect_with_category_models(self, frame: np.ndarray) -> List[Dict]:
        """카테고리별 모델로 상품을 감지합니다 (느림)"""
        detected_products = []

        for category, model in self.models.items():
            try:
                results = model(frame, conf=self.confidence_threshold)

                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        # Bounding box 좌표
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])

                        # 클래스 이름 가져오기
                        class_name = model.names[class_id]

                        detected_products.append(
                            {
                                "category": category,
                                "name": class_name,
                                "confidence": confidence,
                                "bbox": (int(x1), int(y1), int(x2), int(y2)),
                                "class_id": class_id,
                            }
                        )
            except Exception as e:
                print(f"Error detecting {category}: {e}")

        return detected_products

    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        감지된 상품을 프레임에 그립니다

        Args:
            frame: 입력 이미지 프레임
            detections: 감지된 상품 정보 리스트

        Returns:
            표시된 이미지 프레임
        """
        annotated_frame = frame.copy()

        for detection in detections:
            bbox = detection["bbox"]
            x1, y1, x2, y2 = bbox

            # 바운딩 박스 그리기
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 레이블 텍스트
            label = f"{detection['name']} ({detection['confidence']:.2f})"

            # 텍스트 배경
            (text_width, text_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )
            cv2.rectangle(
                annotated_frame,
                (x1, y1 - text_height - 10),
                (x1 + text_width, y1),
                (0, 255, 0),
                -1,
            )

            # 텍스트
            cv2.putText(
                annotated_frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2,
            )

        return annotated_frame

    def get_product_info(self, product_name: str) -> Dict:
        """
        상품 이름으로 상품 정보를 가져옵니다

        Args:
            product_name: 상품 이름

        Returns:
            상품 정보 딕셔너리
        """
        products = self.config.products

        for category in ["icecream", "snack", "ramen"]:
            category_products = products.get(category, [])
            for product in category_products:
                if product["name"] == product_name:
                    return {
                        "name": product["name"],
                        "price": product["price"],
                        "image": product["image"],
                        "category": category,
                    }

        return None
