# YOLO 모델 학습 가이드

## 상품 인식 모델 학습 방법

### 방식 1: 통합 모델 (권장) ⭐

모든 상품을 **하나의 모델**에서 학습합니다.

#### 1. 데이터셋 구조
```
dataset/
├── images/
│   ├── train/
│   │   ├── img001.jpg
│   │   ├── img002.jpg
│   │   └── ...
│   └── val/
│       ├── img101.jpg
│       └── ...
└── labels/
    ├── train/
    │   ├── img001.txt  # 0 0.5 0.5 0.2 0.3  (class_id x y w h)
    │   └── ...
    └── val/
        └── ...
```

#### 2. data.yaml 파일
```yaml
path: /path/to/dataset
train: images/train
val: images/val

nc: 9  # 클래스 개수
names:
  0: 바닐라 아이스크림
  1: 초코 아이스크림
  2: 딸기 아이스크림
  3: 포테토칩
  4: 새우깡
  5: 초코파이
  6: 신라면
  7: 진라면
  8: 안성탕면
```

#### 3. 학습 코드
```python
from ultralytics import YOLO

# YOLOv8 모델 로드
model = YOLO('yolov8n.pt')  # nano, small, medium, large 중 선택

# 학습 실행
results = model.train(
    data='data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='products_all',
    device=0  # GPU 사용
)

# 학습된 모델은 runs/detect/products_all/weights/best.pt 에 저장됨
```

#### 4. 모델 배치
```bash
# 학습된 모델을 프로젝트에 복사
cp runs/detect/products_all/weights/best.pt models/product_yolo/products_all.pt
```

#### 5. config.yaml 설정
```yaml
yolo:
  product:
    unified_model: "models/product_yolo/products_all.pt"
    use_unified: true  # 통합 모델 사용
```

**장점:**
- ✅ 1번 inference로 모든 상품 인식 (빠름)
- ✅ 메모리 효율적 (1개 모델만 로드)
- ✅ 유지보수 용이
- ✅ 일반적인 YOLO 학습 방식

---

### 방식 2: 카테고리별 모델 (비권장)

각 카테고리마다 **별도 모델**을 학습합니다.

#### 1. 아이스크림 모델 학습
```yaml
# icecream_data.yaml
nc: 3
names:
  0: 바닐라 아이스크림
  1: 초코 아이스크림
  2: 딸기 아이스크림
```

```python
model = YOLO('yolov8n.pt')
model.train(data='icecream_data.yaml', epochs=100, name='icecream')
```

#### 2. 과자 모델 학습
```yaml
# snack_data.yaml
nc: 3
names:
  0: 포테토칩
  1: 새우깡
  2: 초코파이
```

```python
model = YOLO('yolov8n.pt')
model.train(data='snack_data.yaml', epochs=100, name='snack')
```

#### 3. 라면 모델 학습
```yaml
# ramen_data.yaml
nc: 3
names:
  0: 신라면
  1: 진라면
  2: 안성탕면
```

```python
model = YOLO('yolov8n.pt')
model.train(data='ramen_data.yaml', epochs=100, name='ramen')
```

#### 4. 모델 배치
```bash
cp runs/detect/icecream/weights/best.pt models/product_yolo/icecream.pt
cp runs/detect/snack/weights/best.pt models/product_yolo/snack.pt
cp runs/detect/ramen/weights/best.pt models/product_yolo/ramen.pt
```

#### 5. config.yaml 설정
```yaml
yolo:
  product:
    use_unified: false  # 카테고리별 모델 사용
    icecream_model: "models/product_yolo/icecream.pt"
    snack_model: "models/product_yolo/snack.pt"
    ramen_model: "models/product_yolo/ramen.pt"
```

**단점:**
- ❌ 3번 inference 필요 (느림)
- ❌ 메모리 사용량 3배
- ❌ 유지보수 어려움

---

## 데이터 라벨링 도구

### Roboflow (권장)
- 웹 기반, 자동 라벨링 지원
- https://roboflow.com

### LabelImg
```bash
pip install labelImg
labelImg
```

### CVAT
- 웹 기반, 협업 가능
- https://cvat.org

---

## 학습 팁

### 1. 데이터 증강 (Augmentation)
```python
model.train(
    data='data.yaml',
    epochs=100,
    # 증강 설정
    hsv_h=0.015,      # 색조 변화
    hsv_s=0.7,        # 채도 변화
    hsv_v=0.4,        # 명도 변화
    degrees=10,       # 회전
    translate=0.1,    # 이동
    scale=0.5,        # 크기
    flipud=0.5,       # 상하 반전
    fliplr=0.5,       # 좌우 반전
)
```

### 2. 이미지 개수
- **최소**: 클래스당 100장
- **권장**: 클래스당 300-500장
- **이상적**: 클래스당 1000장 이상

### 3. 이미지 품질
- 해상도: 640x640 이상
- 다양한 각도, 조명, 배경
- 상품이 화면의 20-80% 차지

### 4. 학습 시간
- CPU: 수십 시간
- GPU (RTX 3060): 1-2시간
- GPU (RTX 4090): 30분

---

## 모델 테스트

### 1. 검증
```python
from ultralytics import YOLO

model = YOLO('models/product_yolo/products_all.pt')
results = model.val(data='data.yaml')
print(f"mAP50: {results.box.map50}")
```

### 2. 예측
```python
results = model.predict(
    source='test_images/',
    conf=0.6,
    save=True
)
```

### 3. 실시간 테스트
```python
import cv2

model = YOLO('models/product_yolo/products_all.pt')
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    results = model(frame)
    annotated = results[0].plot()
    cv2.imshow('YOLO', annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

---

## 문제 해결

### Q: mAP가 낮아요 (< 0.5)
- 데이터 개수 늘리기
- 라벨링 품질 확인
- epoch 증가 (100 → 200)
- 모델 크기 증가 (nano → small)

### Q: 학습이 너무 느려요
- 배치 크기 감소 (16 → 8)
- 이미지 크기 감소 (640 → 416)
- GPU 사용 확인

### Q: 특정 클래스만 잘 못 맞춰요
- 해당 클래스 데이터 추가
- 클래스 불균형 해결 (weight 조정)

---

## 참고 자료

- YOLOv8 공식 문서: https://docs.ultralytics.com
- YOLO 학습 튜토리얼: https://github.com/ultralytics/ultralytics
- 데이터셋 예시: https://universe.roboflow.com
