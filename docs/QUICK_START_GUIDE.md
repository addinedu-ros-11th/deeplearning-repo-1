# 프로그램 실행 및 테스트 가이드

## 📌 목차
1. [전체 시스템 실행 방법 (3대 PC)](#1-전체-시스템-실행-방법-3대-pc)
2. [PC 1대로 테스트하는 방법](#2-pc-1대로-테스트하는-방법)
3. [상품 인식 기능 구현 위치](#3-상품-인식-기능-구현-위치)

---

## 1. 전체 시스템 실행 방법 (3대 PC)

### 1.1 사전 준비

#### 모든 PC에서 공통 작업
```bash
# 1. 프로젝트 클론
cd /home/dh/dev_ws/git_ws
git clone <repository-url> deeplearning-repo-1
cd deeplearning-repo-1

# 2. Python 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 환경변수 설정 (.env 파일 생성)
cp .env.example .env
# .env 파일을 편집하여 DB 정보 입력
```

#### DB 초기화 (한 번만 실행)
```bash
# AWS RDS에 연결하여 스키마 생성
mysql -h <RDS_ENDPOINT> -u <USERNAME> -p < scripts/init_db.sql

# 초기 데이터 삽입
python scripts/seed_data.py
```

#### YOLO 모델 준비
```bash
# models 디렉토리 생성
mkdir -p models/obstacle_detector
mkdir -p models/product_recognizer

# YOLO 모델 파일 배치
# - models/obstacle_detector/best.pt  (장애물 감지용)
# - models/product_recognizer/best.pt (상품 인식용)
```

### 1.2 설정 파일 수정

#### `configs/network_config.yaml`
```yaml
pc1_ai:
  ip: "192.168.1.101"        # AI 서버 IP (실제 PC1 IP로 변경)
  udp_front_port: 6001
  udp_cart_port: 6002

pc2_main:
  ip: "192.168.1.102"        # 메인 허브 IP (실제 PC2 IP로 변경)
  event_port: 5001           # AI 이벤트 수신 포트
  ui_request_port: 5002      # UI 요청 수신 포트
  udp_front_cam_port: 6011   # 전방 카메라 수신 포트
  udp_cart_cam_port: 6012    # 카트 카메라 수신 포트

pc3_ui:
  ip: "192.168.1.103"        # UI 앱 IP (실제 PC3 IP로 변경)
  command_port: 5003         # UI 명령 수신 포트
```

### 1.3 실행 순서

#### **PC1 (AI Server)** - AI 추론 전담
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
source venv/bin/activate
python src/ai_server.py
```

**출력 예시:**
```
Initializing AI Server...
Loading obstacle detection model...
Loading product recognition model...
UDP receivers listening on ports 6001 and 6002
Event client configured to connect to 192.168.1.102:5001
Obstacle UDP loop started.
Product UDP loop started.
Obstacle inference loop started.
Product inference loop started.
```

---

#### **PC2 (Main Hub)** - 중앙 오케스트레이터
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
source venv/bin/activate
python src/main_hub.py
```

**출력 예시:**
```
Initializing Main Hub...
Database connection established
Starting shopping session...
Session ID: 1
TCP servers started (event_port=5001, ui_request_port=5002)
UDP forwarding to AI server started
System ready!
```

---

#### **PC3 (Edge Device)** - 카메라 & UI

**Terminal 1: 카메라 앱**
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
source venv/bin/activate
python src/cart_camera_app.py
```

**출력 예시:**
```
Front camera streaming started
Cart camera streaming started
Streaming frames at 30 FPS...
```

**Terminal 2: UI 대시보드**
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
source venv/bin/activate
python src/cart_ui_app.py
```

**출력 예시:**
```
UI Application started. Connecting to Main Hub at 192.168.1.102
Dashboard window opened
```

---

### 1.4 동작 확인

1. **UI 대시보드**가 화면에 표시됨
2. **카트 내부 카메라**에 상품을 넣으면:
   - AI Server에서 상품 인식
   - Main Hub에서 DB 조회
   - UI에 장바구니 아이템 추가
3. **전방 카메라**에 사람이 지나가면:
   - AI Server에서 장애물 감지
   - Main Hub에서 위험도 판단
   - UI에 경고 표시
4. **체크아웃 버튼** 클릭:
   - DB에 주문 저장
   - UI 초기화

---

## 2. PC 1대로 테스트하는 방법

PC가 1대밖에 없는 경우, 모든 컴포넌트를 동일한 PC에서 실행할 수 있습니다.

### 2.1 설정 변경

#### `configs/network_config.yaml`
```yaml
# 모든 IP를 localhost로 설정
pc1_ai:
  ip: "127.0.0.1"
  udp_front_port: 6001
  udp_cart_port: 6002

pc2_main:
  ip: "127.0.0.1"
  event_port: 5001
  ui_request_port: 5002
  udp_front_cam_port: 6011
  udp_cart_cam_port: 6012

pc3_ui:
  ip: "127.0.0.1"
  command_port: 5003
```

### 2.2 실행 순서 (터미널 4개 사용)

#### Terminal 1: AI Server
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
source venv/bin/activate
python src/ai_server.py
```

#### Terminal 2: Main Hub
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
source venv/bin/activate
python src/main_hub.py
```

#### Terminal 3: 카메라 앱 (웹캠 사용)
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
source venv/bin/activate
python src/cart_camera_app.py
```

**중요**: `cart_camera_app.py`가 카메라 2대를 찾지 못하면 에러 발생
- 해결 방법: 아래 "2.3 카메라 없이 테스트" 참조

#### Terminal 4: UI 앱
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
source venv/bin/activate
python src/cart_ui_app.py
```

### 2.3 카메라 없이 테스트 (녹화 영상 사용)

실제 카메라가 없는 경우, 녹화된 영상 파일로 테스트 가능합니다.

#### 테스트용 영상 스트리머 생성
```bash
# test/video_streamer.py 파일 생성
cat > test/video_streamer.py << 'EOF'
#!/usr/bin/env python3
"""
녹화된 영상 파일을 읽어서 UDP로 전송하는 테스트 스트리머
"""
import cv2
import time
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from network.udp_handler import UDPFrameSender

def stream_video_file(video_path, host, port, fps=30):
    """영상 파일을 UDP로 스트리밍"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video file: {video_path}")
        return
    
    sender = UDPFrameSender(host, port, jpeg_quality=80)
    interval = 1.0 / fps
    
    print(f"Streaming {video_path} to {host}:{port} at {fps} FPS")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            # 영상 끝나면 처음부터 다시
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        
        sender.send_frame(frame)
        time.sleep(interval)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6011)
    parser.add_argument("--fps", type=int, default=30)
    
    args = parser.parse_args()
    
    try:
        stream_video_file(args.video, args.host, args.port, args.fps)
    except KeyboardInterrupt:
        print("\nStreaming stopped")
EOF

chmod +x test/video_streamer.py
```

#### 테스트 영상 준비
```bash
# 테스트 영상 다운로드 또는 자체 제작
# test/yw/data/raw/ 디렉토리에 배치
# - front_camera_test.mp4  (전방 카메라용)
# - cart_camera_test.mp4   (카트 카메라용)
```

#### 영상 스트리머 실행
```bash
# Terminal 3-1: 전방 카메라 스트림
python test/video_streamer.py test/yw/data/raw/front_camera_test.mp4 \
    --host 127.0.0.1 --port 6011 --fps 30

# Terminal 3-2: 카트 카메라 스트림
python test/video_streamer.py test/yw/data/raw/cart_camera_test.mp4 \
    --host 127.0.0.1 --port 6012 --fps 30
```

### 2.4 간단한 통합 테스트 스크립트

```bash
# test/quick_test.sh 파일 생성
cat > test/quick_test.sh << 'EOF'
#!/bin/bash
# 모든 컴포넌트를 백그라운드로 실행하는 테스트 스크립트

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 가상환경 활성화
source venv/bin/activate

# 로그 디렉토리 생성
mkdir -p logs

# 1. AI Server 시작
echo "Starting AI Server..."
python src/ai_server.py > logs/ai_server.log 2>&1 &
AI_PID=$!
sleep 3

# 2. Main Hub 시작
echo "Starting Main Hub..."
python src/main_hub.py > logs/main_hub.log 2>&1 &
MAIN_PID=$!
sleep 3

# 3. 카메라 앱 시작 (웹캠 사용)
echo "Starting Camera App..."
python src/cart_camera_app.py > logs/camera_app.log 2>&1 &
CAM_PID=$!
sleep 2

# 4. UI 앱 시작 (포그라운드)
echo "Starting UI App..."
python src/cart_ui_app.py

# UI 종료 시 모든 프로세스 종료
echo "Shutting down..."
kill $AI_PID $MAIN_PID $CAM_PID 2>/dev/null
echo "All processes stopped"
EOF

chmod +x test/quick_test.sh
```

**실행:**
```bash
./test/quick_test.sh
```

---

## 3. 상품 인식 기능 구현 위치

상품 인식 기능은 여러 파일에 걸쳐 구현되어 있습니다. 각 단계별로 어디를 수정해야 하는지 설명합니다.

### 3.1 핵심 구현 위치

#### 📁 `src/detectors/product_dl.py` - **가장 중요**
**역할**: YOLO 모델을 사용하여 카메라 프레임에서 상품을 인식

**현재 구현:**
```python
from ultralytics import YOLO

class ProductRecognizer:
    def __init__(self, model_path='models/product_recognizer/best.pt'):
        self.model = YOLO(model_path)
        self.threshold = 0.7  # 상품 인식 신뢰도 임계값

    def recognize(self, frame):
        """
        프레임 내의 상품을 인식하여 product_id 반환
        """
        results = self.model.predict(frame, conf=self.threshold, verbose=False)
        
        if len(results) > 0 and len(results[0].boxes) > 0:
            # 가장 신뢰도가 높은 첫 번째 객체 선택
            top_box = results[0].boxes[0]
            product_id = int(top_box.cls[0])
            confidence = float(top_box.conf[0])
            
            return {
                "product_id": product_id,
                "confidence": confidence,
                "status": "detected"
            }
        
        return {"status": "none"}
```

**수정 방법 (더 많은 정보 추출):**
```python
def recognize(self, frame):
    """
    프레임 내의 모든 상품을 인식하여 리스트 반환
    """
    results = self.model.predict(frame, conf=self.threshold, verbose=False)
    
    detected_products = []
    
    if len(results) > 0:
        for box in results[0].boxes:
            product_id = int(box.cls[0])
            confidence = float(box.conf[0])
            bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            
            detected_products.append({
                "product_id": product_id,
                "confidence": confidence,
                "bbox": bbox,  # 바운딩 박스 좌표
                "status": "detected"
            })
    
    return detected_products if detected_products else [{"status": "none"}]
```

**바코드 인식 추가 (OCR 사용):**
```python
import cv2
from pyzbar.pyzbar import decode  # pip install pyzbar

class ProductRecognizer:
    def __init__(self, model_path='models/product_recognizer/best.pt'):
        self.model = YOLO(model_path)
        self.threshold = 0.7

    def recognize(self, frame):
        """YOLO + 바코드 스캔"""
        # 1. YOLO로 상품 영역 검출
        results = self.model.predict(frame, conf=self.threshold, verbose=False)
        
        detected_products = []
        
        if len(results) > 0:
            for box in results[0].boxes:
                # 상품 영역 크롭
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cropped = frame[y1:y2, x1:x2]
                
                # 2. 크롭된 영역에서 바코드 스캔
                barcodes = decode(cropped)
                
                if barcodes:
                    barcode_data = barcodes[0].data.decode('utf-8')
                    detected_products.append({
                        "barcode": barcode_data,
                        "confidence": float(box.conf[0]),
                        "bbox": [x1, y1, x2, y2],
                        "status": "detected"
                    })
                else:
                    # 바코드 없으면 클래스 ID 사용
                    detected_products.append({
                        "product_id": int(box.cls[0]),
                        "confidence": float(box.conf[0]),
                        "bbox": [x1, y1, x2, y2],
                        "status": "detected"
                    })
        
        return detected_products if detected_products else [{"status": "none"}]
```

---

#### 📁 `src/ai_server.py` - AI 추론 루프
**역할**: 카메라 프레임을 받아서 `ProductRecognizer`를 호출하고 결과를 메인 허브로 전송

**현재 구현 (107-135줄):**
```python
def _product_inference_loop(self):
    print("Product inference loop started.")
    while True:
        with self._product_lock:
            jpeg = self._latest_product_bytes
        
        if jpeg is None:
            time.sleep(0.1)
            continue

        frame = self._decode(jpeg)
        if frame is None:
            continue

        result = self.product_model.recognize(frame)
        
        # If a product is detected
        if result.get("status") == "detected":
            product_id = result.get("product_id")
            confidence = result.get("confidence", 0.0)
            
            msg = Protocol.make_event(
                event_type=AIEvent.PRODUCT_DETECTED,
                data={
                    "product_id": product_id,
                    "confidence": confidence,
                }
            )
            self._push_event(msg)
        
        time.sleep(0.1)
```

**수정 예시 (다중 상품 처리):**
```python
def _product_inference_loop(self):
    print("Product inference loop started.")
    while True:
        with self._product_lock:
            jpeg = self._latest_product_bytes
        
        if jpeg is None:
            time.sleep(0.1)
            continue

        frame = self._decode(jpeg)
        if frame is None:
            continue

        # recognize()가 이제 리스트를 반환
        results = self.product_model.recognize(frame)
        
        # 감지된 모든 상품에 대해 이벤트 전송
        for result in results:
            if result.get("status") == "detected":
                # barcode 또는 product_id 사용
                identifier = result.get("barcode") or result.get("product_id")
                confidence = resultmodels/product_recognizer/product_yolo8s.pt.get("confidence", 0.0)
                
                msg = Protocol.make_event(
                    event_type=AIEvent.PRODUCT_DETECTED,
                    data={
                        "identifier": identifier,  # barcode 또는 product_id
                        "confidence": confidence,
                        "bbox": result.get("bbox"),  # 시각화용
                    }
                )
                self._push_event(msg)
        
        time.sleep(0.1)
```

---

#### 📁 `src/core/engine.py` - 비즈니스 로직
**역할**: AI에서 받은 이벤트를 처리하고 DB에 저장, UI 업데이트

**현재 구현 (추정 위치):**
```python
def process_product_event(self, event_data):
    """
    상품 감지 이벤트 처리
    - Debouncing (중복 방지)
    - DB에서 상품 정보 조회
    - 장바구니에 추가
    - UI에 명령 전송
    """
    product_id = event_data.get("product_id")
    
    # Debouncing: 같은 상품이 5초 이내에 재감지되면 무시
    current_time = time.time()
    if product_id in self._last_product_time:
        if current_time - self._last_product_time[product_id] < 5.0:
            return  # 중복 감지, 무시
    
    self._last_product_time[product_id] = current_time
    
    # DB에서 상품 정보 조회
    product = self.product_dao.get_product_by_id(product_id)
    if not product:
        print(f"Unknown product_id: {product_id}")
        return
    
    # 장바구니에 추가
    self.tx_dao.add_cart_item(
        session_id=self.current_session_id,
        product_id=product_id,
        quantity=1
    )
    
    # UI 업데이트 명령 전송
    cart_items = self.tx_dao.get_cart_items(self.current_session_id)
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    ui_msg = Protocol.make_command(
        command_type=UICommand.UPDATE_CART,
        data={
            "items": cart_items,
            "total": total
        }
    )
    self.ui_client.send(ui_msg)
```

**바코드 기반 처리로 수정:**
```python
def process_product_event(self, event_data):
    """바코드 기반 상품 처리"""
    identifier = event_data.get("identifier")
    
    # Debouncing
    current_time = time.time()
    if identifier in self._last_product_time:
        if current_time - self._last_product_time[identifier] < 5.0:
            return
    
    self._last_product_time[identifier] = current_time
    
    # DB에서 상품 조회 (barcode 또는 product_id)
    if isinstance(identifier, str) and len(identifier) > 8:
        # 바코드로 추정
        product = self.product_dao.get_product_by_barcode(identifier)
    else:
        # product_id로 추정
        product = self.product_dao.get_product_by_id(identifier)
    
    if not product:
        print(f"Unknown product: {identifier}")
        return
    
    # 장바구니에 추가 (나머지 동일)
    # ...
```

---

#### 📁 `src/database/product_dao.py` - DB 조회
**역할**: 상품 정보를 DB에서 가져오기

**현재 구현:**
```python
class ProductDAO:
    def __init__(self, db_handler):
        self.db = db_handler
    
    def get_product_by_id(self, product_id):
        """product_id로 상품 조회"""
        query = "SELECT * FROM products WHERE id = %s"
        result = self.db.execute_query(query, (product_id,))
        return result[0] if result else None
    
    def get_product_by_barcode(self, barcode):
        """barcode로 상품 조회"""
        query = "SELECT * FROM products WHERE barcode = %s"
        result = self.db.execute_query(query, (barcode,))
        return result[0] if result else None
```

---

### 3.2 YOLO 모델 학습 (필요한 경우)

상품 인식 정확도를 높이려면 커스텀 모델 학습이 필요합니다.

#### 데이터셋 준비
```bash
# 디렉토리 구조
dataset/
  train/
    images/
      product_001.jpg
      product_002.jpg
    labels/
      product_001.txt  # YOLO 형식
      product_002.txt
  val/
    images/
    labels/
```

#### YOLO 학습 스크립트
```python
# scripts/train_product_model.py
from ultralytics import YOLO

# 사전 학습된 모델 로드
model = YOLO('yolov8n.pt')

# 학습
results = model.train(
    data='dataset/product_data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='product_recognizer',
    project='models'
)

# 모델 저장
model.save('models/product_recognizer/best.pt')
```

#### `dataset/product_data.yaml`
```yaml
train: dataset/train/images
val: dataset/val/images

nc: 50  # 상품 클래스 개수
names:
  0: banana
  1: milk
  2: bread
  3: apple
  # ... 50개까지
```

---

### 3.3 실시간 디버깅 (시각화)

상품 인식이 제대로 작동하는지 확인하려면 시각화 도구를 추가하세요.

#### `src/detectors/product_dl.py`에 시각화 추가
```python
def recognize_with_visualization(self, frame):
    """인식 결과를 프레임에 그려서 반환"""
    results = self.model.predict(frame, conf=self.threshold, verbose=False)
    
    detected_products = []
    annotated_frame = frame.copy()
    
    if len(results) > 0:
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            
            # 바운딩 박스 그리기
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 텍스트 표시
            label = f"Product {class_id}: {confidence:.2f}"
            cv2.putText(annotated_frame, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            detected_products.append({
                "product_id": class_id,
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2]
            })
    
    return detected_products, annotated_frame
```

#### 테스트 스크립트
```python
# test/test_product_recognition.py
import cv2
from detectors.product_dl import ProductRecognizer

recognizer = ProductRecognizer()
cap = cv2.VideoCapture(0)  # 웹캠

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    products, annotated = recognizer.recognize_with_visualization(frame)
    
    # 결과 출력
    for p in products:
        print(f"Detected: {p}")
    
    # 화면에 표시
    cv2.imshow('Product Recognition', annotated)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

**실행:**
```bash
python test/test_product_recognition.py
```

---

## 요약

### 전체 실행 (3대 PC)
1. **PC1**: `python src/ai_server.py`
2. **PC2**: `python src/main_hub.py`
3. **PC3**: `python src/cart_camera_app.py` + `python src/cart_ui_app.py`

### PC 1대 테스트
- 모든 IP를 `127.0.0.1`로 설정
- 4개 터미널에서 각각 실행
- 카메라 없으면 `test/video_streamer.py` 사용

### 상품 인식 구현 위치
1. **`src/detectors/product_dl.py`** ← 가장 중요 (YOLO 모델 사용)
2. **`src/ai_server.py`** ← 추론 루프, 이벤트 전송
3. **`src/core/engine.py`** ← 비즈니스 로직, DB 처리
4. **`src/database/product_dao.py`** ← DB 조회

**핵심**: `product_dl.py`의 `recognize()` 메서드만 수정하면 나머지는 자동으로 연동됩니다!
