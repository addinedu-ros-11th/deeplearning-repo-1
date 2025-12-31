# YOLO OBB 모델 학습 파이프라인

이 디렉토리는 YOLO OBB(Oriented Bounding Box) 모델을 학습시키고, 평가, 사용하는 전체 파이프라인을 위한 스크립트들을 포함합니다.

---

## 🚀 파이프라인 실행 순서

아래 스크립트들을 순서대로 실행하여 모델을 빌드하세요.

### 1. 데이터 준비

- **CVAT에서 데이터 라벨링**:
  - 객체 라벨링 시 **회전된 사각형(rotated rectangle)** 또는 **다각형(polygon)** 도구를 사용하여 OBB(Oriented Bounding Box) 형태로 라벨링합니다.
  - 라벨링 완료 후, `CVAT for image` 형식으로 데이터를 내보내기(export)합니다.
- **데이터 배치**:
  - 내보내기한 `annotations.xml` 파일과 `images` 폴더를 `test/yw1/data/raw/` 디렉토리 안에 복사합니다.
  - 최종 경로는 다음과 같아야 합니다:
    - `test/yw1/data/raw/annotations.xml`
    - `test/yw1/data/raw/images/image1.jpg`
    - `test/yw1/data/raw/images/image2.png`
    - ...

### 2. `01_preprocess_data.py`

- **목적**: CVAT에서 받은 XML 형식의 라벨링 데이터를 YOLO OBB가 요구하는 형식(`.txt` 파일)으로 변환합니다.
- **실행 전**: 스크립트 내의 `CLASS_MAPPING` 딕셔너리를 자신의 데이터셋 클래스에 맞게 수정해야 합니다.
- **실행**: `python test/yw1/scripts/01_preprocess_data.py`
- **결과**: `test/yw1/data/processed/` 폴더에 변환된 `images`와 `labels`가 생성됩니다.

### 3. `02_split_dataset.py`

- **목적**: 전처리된 전체 데이터셋을 `train`, `val`, `test` 세트로 분할합니다.
- **실행 전**: 스크립트 상단의 `TRAIN_RATIO`, `VAL_RATIO`, `TEST_RATIO`를 필요에 따라 조절할 수 있습니다. (기본: 80/10/10)
- **실행**: `python test/yw1/scripts/02_split_dataset.py`
- **결과**: `processed` 폴더의 `images`와 `labels` 하위에 `train`, `val`, `test` 폴더가 생성되고 파일들이 분배됩니다.

### 4. `03_train.py`

- **목적**: `yolov8n-obb.pt` 모델을 기반으로 데이터셋 학습을 시작합니다.
- **실행 전**: `EPOCHS`, `IMG_SIZE`, `BATCH_SIZE` 등 학습 관련 하이퍼파라미터를 조정할 수 있습니다.
- **실행**: `python test/yw1/scripts/03_train.py`
- **결과**: 학습 로그, 결과, 그리고 모델 가중치(`best.pt`, `last.pt`)가 `test/yw1/runs/train/yolo_obb_training/expN` 폴더에 저장됩니다.

### 5. `04_validate.py`

- **목적**: 학습된 모델의 성능을 검증 세트(validation set)를 사용하여 평가합니다. mAP와 같은 지표를 확인할 수 있습니다.
- **실행 전**: 스크립트 상단의 `RUN_NAME`을 `03_train.py` 실행 결과로 생성된 폴더 이름(예: `exp1`)으로 정확히 수정해야 합니다.
- **실행**: `python test/yw1/scripts/04_validate.py`
- **결과**: 평가 결과가 터미널에 출력되고, 관련 데이터는 `test/yw1/runs/val/` 폴더에 저장됩니다.

### 6. `05_predict.py`

- **목적**: 학습된 모델을 사용하여 새로운 이미지에 대한 객체 탐지를 수행합니다.
- **실행 전**:
  - `test/yw1/data/inference/input/` 폴더에 예측을 원하는 이미지 파일들을 넣으세요.
  - 스크립트 상단의 `RUN_NAME`을 사용하려는 모델이 있는 폴더 이름으로 정확히 수정해야 합니다.
- **실행**: `python test/yw1/scripts/05_predict.py`
- **결과**:
  - **시각화된 이미지**: `test/yw1/data/inference/output/` 폴더에 바운딩 박스가 그려진 이미지 파일이 저장됩니다.
  - **예측 특성(좌표 등)**: 같은 폴더 내의 `labels` 하위 폴더에 각 이미지별로 탐지된 객체의 클래스, 신뢰도, OBB 좌표가 담긴 `.txt` 파일이 생성됩니다.
---
