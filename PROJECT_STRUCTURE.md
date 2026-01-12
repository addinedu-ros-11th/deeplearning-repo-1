# 프로젝트 구조 문서

이 문서는 `src/` 디렉토리의 Python 소스 파일에 대한 상세한 개요를 제공하며, AI 스마트 쇼핑카트 시스템의 각 컴포넌트의 목적과 연결 관계를 설명합니다.

---

## 📁 디렉토리 구조

```
src/
├── 📄 main_hub.py                  # 메인 허브 애플리케이션 (PC2 - 중앙 서버)
├── 📄 ai_server.py                 # AI 서버 애플리케이션 (PC1 - 추론 서버)
├── 📄 cart_camera_app.py           # 카메라 스트리밍 애플리케이션 (PC3)
├── 📄 cart_ui_app.py               # UI 대시보드 애플리케이션 (PC3)
├── 📄 cart_ui_app_v2.py            # UI 대시보드 v2 (레거시)
│
├── 📁 common/                      # 공통 설정 및 프로토콜
│   ├── config.py                   # 설정 로더 (Pydantic 기반)
│   └── protocols.py                # 통신 프로토콜 정의 및 메시지 타입
│
├── 📁 core/                        # 핵심 비즈니스 로직
│   └── engine.py                   # SmartCartEngine - 쇼핑카트 핵심 로직
│
├── 📁 database/                    # 데이터베이스 접근 계층
│   ├── db_handler.py               # DBHandler - PyMySQL 래퍼
│   ├── product_dao.py              # ProductDAO - 상품 정보 쿼리
│   ├── transaction_dao.py          # TransactionDAO - 거래 및 장바구니 관리
│   └── obstacle_log_dao.py         # ObstacleLogDAO - 장애물 감지 로깅
│
├── 📁 detectors/                   # AI 탐지 및 인식 모듈
│   ├── obstacle_dl.py              # ObstacleDetector - YOLO 기반 장애물 감지
│   ├── product_dl.py               # ProductRecognizer - YOLO 기반 상품 인식
│   ├── obstacle_logger.py          # 장애물 감지 로깅 유틸리티
│   ├── obstacle_tracker.py         # 장애물 추적 및 위험도 계산
│   └── risk_engine.py              # 위험 평가 엔진
│
├── 📁 network/                     # 네트워크 통신 모듈
│   ├── tcp_server.py               # TCPServer - 멀티스레드 TCP 서버
│   ├── tcp_client.py               # TCPClient - TCP 클라이언트
│   └── udp_handler.py              # UDP 프레임 송수신 (UDPFrameSender, UDPFrameReceiver)
│
├── 📁 ui/                          # UI 및 대시보드
│   ├── dashboard.py                # CartDashboard - PyQt6 UI (v1)
│   ├── dashboard_v2.py             # CartDashboard v2 (최신 버전)
│   ├── ui_controller.py            # UIController - UI 제어 로직 (v1)
│   └── ui_controller_v2.py         # UIController v2 (최신 버전)
│
└── 📁 utils/                       # 유틸리티 함수 모음
    ├── logger.py                   # SystemLogger - 로깅 설정
    └── image_proc.py               # ImageProcessor - 이미지 처리 유틸리티
```

---

## Ⅰ. 메인 애플리케이션

세 개의 컴퓨터 시스템 각각의 주요 실행 진입점입니다.

### main_hub.py

- **`MainPC2Hub`**
    - **기능**: 전체 시스템의 중앙 서버 및 오케스트레이터 (PC2에서 실행). 모든 다른 컴포넌트를 연결하는 게이트웨이 역할을 합니다.
        - 데이터베이스 연결 및 데이터 접근 객체(DAO) 초기화
        - 쇼핑 세션 시작
        - **UDP 포워딩**: 카트 카메라 앱(PC3)에서 카메라 스트림을 수신하고 AI 서버(PC1)로 전달
        - **AI 이벤트 처리**: TCP 서버를 실행하여 AI 서버에서 비동기 감지 이벤트(장애물, 상품) 수신
        - **UI 요청 처리**: TCP 서버를 실행하여 UI 앱에서 동기식 요청(예: 결제) 처리
        - **비즈니스 로직**: `SmartCartEngine`을 사용하여 들어오는 이벤트 처리 및 의사결정
        - **UI 명령 전송**: `TCPClient`를 사용하여 명령(예: 장바구니 업데이트, 알람 표시) 전송
    - **주요 메서드**:
        - `run()`: 모든 서버 및 포워딩 스레드 시작
        - `handle_ai_event()`: AI 서버로부터의 메시지 처리
        - `handle_ui_request()`: UI 앱으로부터의 메시지 처리
        - `forward_front_cam() / forward_cart_cam()`: UDP 포워딩 로직
    - **의존성**: `SmartCartEngine`, `DBHandler`, 모든 DAOs, `TCPServer`, `TCPClient`, `UDPFrameSender`, `UDPFrameReceiver`, `config`, `protocols`

### ai_server.py

- **`AIServer`**
    - **기능**: AI 추론 컴퓨터(PC1) 메인 애플리케이션. 비디오 스트림을 수신하고 객체 감지를 수행한 후 결과를 메인 허브로 전송합니다.
        - **UDP 리스너**: 메인 허브로부터 전면(장애물)과 카트(상품) 카메라 스트림을 별도 스레드에서 수신
        - **추론 루프**: 각 스트림의 최신 프레임에서 적절한 YOLO 모델을 사용하여 연속 추론을 수행하는 두 개의 별도 스레드 실행
        - **이벤트 전송**: 충분한 신뢰도로 객체 감지 시, `Protocol` 클래스를 사용하여 메시지를 포맷하고 `TCPClient`를 통해 메인 허브로 전송
    - **주요 메서드**:
        - `run()`: 모든 UDP 리스닝 및 추론 스레드 시작
        - `_obstacle_inference_loop()`: 장애물 감지 연속 실행
        - `_product_inference_loop()`: 상품 인식 연속 실행
        - `_push_event()`: 감지된 이벤트를 메인 허브로 전송
    - **의존성**: `ObstacleDetector`, `ProductRecognizer`, `UDPFrameReceiver`, `TCPClient`, `config`, `protocols`

### cart_camera_app.py

- **`CartEdgeApp`**
    - **기능**: 카메라 스트림 담당 카트의 엣지 컴퓨터(PC3) 애플리케이션입니다.
        - **카메라 캡처**: 두 개의 별도 하드웨어 카메라(`cv2.VideoCapture`)에서 비디오 캡처
        - **UDP 스트리밍**: 각 프레임을 JPEG로 압축하고 별도 스레드에서 `UDPFrameSender`를 사용하여 메인 허브로 전송
    - **주요 메서드**:
        - `run()`: 두 개의 카메라 스트리밍 스레드 시작
        - `stream_front_camera()`: 장애물 감지용 프레임 캡처 및 전송
        - `stream_cart_camera()`: 상품 인식용 프레임 캡처 및 전송
    - **의존성**: `UDPFrameSender`, `ImageProcessor`, `config`, `cv2`

### cart_ui_app.py

- **`main()`**
    - **기능**: 카트 컴퓨터(PC3)에서 실행되는 PyQt6 기반 UI 애플리케이션의 주 진입점입니다.
        - Qt 애플리케이션 환경 초기화
        - `CartDashboard` (뷰) 생성
        - `UIController` 생성 (대시보드를 메인 허브에 연결)
        - 대시보드 창 표시 및 애플리케이션 이벤트 루프 시작
    - **의존성**: `CartDashboard`, `UIController`, `PyQt6`

---

## Ⅱ. 핵심 비즈니스 로직

### core/engine.py

- **`SmartCartEngine`**
    - **기능**: 쇼핑카트의 핵심 비즈니스 로직을 캡슐화하여 이벤트 기반의 의사결정을 수행합니다. 네트워크 또는 UI 관련 사항에 대해 상태를 갖지 않도록 설계되었습니다.
        - **이벤트 처리**: 장애물이나 상품 감지 시 수행할 작업의 로직 포함
        - **디바운싱**: 같은 상품이 단시간에 여러 번 감지된 경우 중복 추가 방지
        - **상태 관리**: 마지막 감지된 장애물 수준 등의 단순 상태 관리로 중복 UI 알람 방지
    - **메서드**:
        - `process_obstacle_event()`: 장애물 로깅, 위험도 변경 확인, 필요시 UI 알람 전송
        - `process_product_event()`: 감지 디바운싱, DB에서 상품 정보 조회, 장바구니에 항목 추가, UI 업데이트 명령 전송
        - `reset()`: 결제 시 엔진의 내부 상태 초기화
    - **의존성**: 모든 DAOs, `TCPClient` (UI와의 통신용)
    - **생성 위치**: `main_hub.py`

---

## Ⅲ. 네트워크 통신

### network/tcp_server.py

- **`TCPServer`**
    - **기능**: 길이 접두사 JSON 메시지를 처리하는 일반적인 멀티스레드 TCP 서버. 각 들어오는 연결에 대해 새로운 스레드를 생성하여 요청을 처리합니다.
    - **프로토콜**: `[4-바이트 길이][JSON 페이로드]`
    - **메서드**:
        - `start()`: 포트에 바인드하고 들어오는 연결을 무한정 대기
        - `_client_handler()`: 요청을 수신하고 초기화 중에 제공된 핸들러 함수로 전달한 후 응답을 클라이언트로 다시 전송
    - **사용 위치**:
        - `main_hub.py`: 두 개의 인스턴스 생성 (AI 이벤트용, UI 요청용)
        - `ui_controller.py`: 메인 허브로부터의 명령 수신용

### network/tcp_client.py

- **`TCPClient`**
    - **기능**: 길이 접두사 JSON 메시지를 전송하고 응답을 대기하는 일반적인 TCP 클라이언트입니다.
    - **메서드**:
        - `send_request()`: 서버에 연결하고 데이터를 전송한 후 응답을 대기하여 반환. 타임아웃 및 연결 오류에 대한 오류 처리 포함
    - **사용 위치**:
        - `ai_server.py`: 메인 허브로 이벤트 전송용
        - `main_hub.py`: 카트 UI 앱으로 명령 전송용

### network/udp_handler.py

- **`UDPFrameSender` / `UDPFrameReceiver`**
    - **기능**: UDP 패킷 크기 제한을 고려하여 큰 데이터(비디오 프레임 등)를 UDP로 전송하기 위해 설계된 클래스 쌍입니다.
    - **`UDPFrameSender`**:
        - 비디오 프레임을 JPEG 바이너리로 압축
        - 바이너리 데이터를 UDP 패킷에 적합한 더 작은 청크로 분할
        - 각 청크에 헤더(`frame_id`, `chunk_id`, `total_chunks`) 첨부 후 전송
    - **`UDPFrameReceiver`**:
        - UDP 패킷 수신 대기
        - 헤더 정보를 기반으로 각 `frame_id`에 대한 청크 재조립
        - 모든 프레임 청크 수신 후 결합하여 완전한 JPEG 바이너리 데이터 생성
    - **사용 위치**:
        - `cart_camera_app.py`: `UDPFrameSender` 사용
        - `main_hub.py`: `UDPFrameReceiver` (카메라 앱에서 프레임 수신), `UDPFrameSender` (AI 서버로 포워드) 모두 사용
        - `ai_server.py`: `UDPFrameReceiver` 사용

---

## Ⅳ. 데이터베이스 계층

### database/db_handler.py

- **`DBHandler`**
    - **기능**: 데이터베이스 상호작용을 단순화하기 위한 `pymysql` 라이브러리의 래퍼입니다.
        - 데이터베이스 연결 관리
        - 자동 커밋/롤백을 사용한 쿼리 실행 메서드 제공
        - `DictCursor`를 사용하여 쿼리 결과를 Python 딕셔너리로 반환
    - **메서드**:
        - `execute()`: `UPDATE`/`DELETE` 쿼리용
        - `insert()`: `INSERT` 쿼리용; 새로 생성된 행의 ID 반환
        - `fetch_one()` / `fetch_all()`: `SELECT` 쿼리용
        - `begin()`, `commit()`, `rollback()`, `close()`: 수동 트랜잭션 제어용
    - **생성 위치**: `main_hub.py`

### database/*_dao.py

- **`ProductDAO`, `TransactionDAO`, `ObstacleLogDAO`**
    - **기능**: 데이터 접근 객체(DAO) 집합. 각 DAO는 특정 도메인(상품, 거래, 로그)과 관련된 SQL 쿼리를 캡슐화하여 나머지 애플리케이션에 깔끔한 메서드 기반 API를 제공합니다. 모두 쿼리 실행을 위해 `DBHandler` 인스턴스를 사용합니다.
    - **`ProductDAO`**: 상품 정보 조회 및 재고 관리
    - **`TransactionDAO`**: 쇼핑 세션, 장바구니 항목, 결제 주문 관리
    - **`ObstacleLogDAO`**: 데이터베이스에 장애물 감지 이벤트 기록
    - **생성 위치**: `main_hub.py`

---

## Ⅴ. AI 및 탐지

### detectors/obstacle_dl.py

- **`ObstacleDetector`**
    - **기능**: 장애물 감지용으로 학습된 YOLO 모델을 로드합니다.
    - **메서드**:
        - `detect()`: 단일 이미지 프레임을 입력받아 추론을 실행하고 계산된 `danger_level` (경계 상자 크기 기반)과 감지된 객체 목록을 포함하는 딕셔너리 반환
    - **사용 위치**: `ai_server.py`

### detectors/product_dl.py

- **`ProductRecognizer`**
    - **기능**: 상품 인식용으로 학습된 YOLO 모델을 로드합니다.
    - **메서드**:
        - `recognize()`: 단일 이미지 프레임을 입력받아 추론을 실행하고 가장 높은 신뢰도로 감지된 상품의 클래스 ID 반환. 이 ID는 데이터베이스의 `product_id`에 해당합니다.
    - **사용 위치**: `ai_server.py`

### detectors/obstacle_logger.py

- **`ObstacleLogger`**
    - **기능**: 장애물 감지 이벤트 로깅 및 기록 유틸리티
    - **주요 기능**: 감지된 장애물 정보를 구조화하여 데이터베이스에 저장

### detectors/obstacle_tracker.py

- **`ObstacleTracker`**
    - **기능**: 감지된 장애물의 추적 및 위험도 계산
    - **주요 기능**: 시간 경과에 따른 장애물 위치 추적 및 위험 수준 평가

### detectors/risk_engine.py

- **`RiskEngine`**
    - **기능**: 감지된 장애물 정보를 기반으로 위험도 평가 및 알람 판단
    - **주요 기능**: 복잡한 위험 평가 로직 처리

---

## Ⅵ. 사용자 인터페이스

### ui/dashboard.py

- **`CartDashboard`**
    - **기능**: PyQt6로 구축된 UI의 메인 윈도우. 이 클래스는 UI 요소의 시각적 표현 및 레이아웃만 담당하며 애플리케이션 로직을 포함하지 않습니다.
    - **공개 API**: `add_product()`, `set_danger_level()`, `reset_cart()` 등의 메서드 제공 (UIController에서 호출하여 디스플레이 업데이트)
    - **신호**: 버튼(예: "카트 시작") 클릭 시 신호를 발생시키며, `UIController`가 이를 수신합니다.
    - **사용 위치**: `cart_ui_app.py` (인스턴스 생성), `ui_controller.py` (제어)

### ui/dashboard_v2.py

- **`CartDashboard` (v2)**
    - **기능**: 최신 버전의 PyQt6 기반 UI 대시보드 (개선된 레이아웃 및 기능)
    - **특징**: v1 대시보드의 개선 버전

### ui/ui_controller.py

- **`UIController`**
    - **기능**: UI 애플리케이션의 "뇌"로서 시각적 `CartDashboard`와 `MainPC2Hub` 사이의 다리 역할을 합니다.
        - **UI 명령 수신**: 백그라운드 TCP 서버를 실행하여 메인 허브로부터의 명령(예: "장바구니에 상품 추가") 수신
        - **안전한 UI 업데이트**: 수신한 네트워크 명령을 Qt 신호(`pyqtSignal`)로 변환하여 스레드 안전한 UI 업데이트 보장
        - **사용자 작업 처리**: `CartDashboard`로부터의 버튼 클릭 신호 수신 및 해당 요청을 메인 허브의 요청 포트로 전송
    - **생성 위치**: `cart_ui_app.py`

### ui/ui_controller_v2.py

- **`UIController` (v2)**
    - **기능**: 최신 버전의 UI 제어 로직 (개선된 신호 처리 및 이벤트 관리)
    - **특징**: v1 UI 컨트롤러의 개선 버전

---

## Ⅶ. 공통 및 유틸리티

### common/config.py

- **`Config`**
    - **기능**: Pydantic 기반 설정 로더로 `/configs` 디렉토리의 모든 `.yaml` 파일을 읽습니다. 설정을 검증하고 자동완성이 가능한 타입 안전 `config` 객체를 제공하여 애플리케이션 전체에서 사용할 수 있습니다.

### common/protocols.py

- **`Protocol` 및 열거형**
    - **기능**: 시스템의 모든 TCP 기반 통신의 구조 및 상수를 정의합니다.
    - **`Protocol` 클래스**: 일관되게 포맷된 JSON 메시지 딕셔너리를 생성하기 위한 정적 메서드 제공 (예: `Protocol.ai_event(...)`) 및 검증/파싱 함수 포함
    - **열거형**: (`MessageType`, `AIEvent`, `UICommand` 등) 모든 메시지 타입 및 명령에 대한 명확한 정수 기반 상수 제공 (마법의 문자열 방지)

---

## Ⅷ. 유틸리티

### utils/logger.py

- **`SystemLogger`**
    - **기능**: Python의 내장 `logging` 모듈을 위한 간단한 래퍼. 파일(`logs/system.log`)과 콘솔 모두에 로깅을 설정하며, 각각에 대해 서로 다른 포맷팅을 제공합니다.

### utils/image_proc.py

- **`ImageProcessor`**
    - **기능**: `OpenCV`를 사용한 이미지 작업을 위한 정적 유틸리티 메서드 모음
    - **메서드**: `encode_frame` (OpenCV 프레임 → JPEG 바이트), `decode_frame` (바이트 → 프레임), `resize_for_ai`, `draw_labels` (디버깅용)

---

## 시스템 아키텍처

### 데이터 흐름

```
카메라 (PC3) 
    ↓ (UDP 프레임)
메인 허브 (PC2)
    ├→ (UDP 포워드) → AI 서버 (PC1)
    │    ↓ (TCP 이벤트)
    └← TCP 명령 ← UI (PC3)
```

### 통신 프로토콜

- **TCP**: 길이 접두사 JSON (제어 메시지 및 이벤트)
  - 포맷: `[4-바이트 길이][JSON 페이로드]`
- **UDP**: 청크 JPEG 프레임 (카메라 스트림)
  - 구조: `frame_id`, `chunk_id`, `total_chunks` 포함

### 스레딩 모델

- **ai_server.py**: 4개 스레드 (2개 UDP 리스너, 2개 추론 루프)
- **main_hub.py**: 6개 이상 스레드 (2개 UDP 리스너, 2개 UDP 포워더, 2개 TCP 서버)
- 모든 네트워크 I/O는 별도 스레드에서 실행

---

## 개발 워크플로우

### 시스템 실행

**단일 PC 테스트 (개발 권장):**
```bash
python test/run_hybrid_test.py  # 모든 4개 컴포넌트를 자동으로 시작
```

**멀티 PC 배포 (순서대로 시작):**
```bash
# PC1 (AI 서버)
python src/ai_server.py

# PC2 (메인 허브)
python src/main_hub.py

# PC3 (UI + 카메라 - 별도 터미널)
python src/cart_ui_app.py
python src/cart_camera_app.py
```

### 하드웨어 없이 테스트

- **카메라 없음**: `test/optimized_hybrid_camera.py` 사용 (비디오 파일 + 웹캠 폴백)
- **UI 테스트**: `test/test_ui_update.py` (UI에 모의 UPDATE_CART 명령 전송)
- 모든 네트워크 설정은 단일 PC 테스트를 위해 localhost 기본값 사용

### 디버깅

- **로그**: `logs/system.log` (모든 컴포넌트), 또는 테스트 실행용 `test_*.log` 파일
- **UDP 프레임 흐름**: "Received N frames, latest size: X bytes" 콘솔 출력 확인
- **프로토콜 문제**: JSON 구조가 `protocols.py` 열거형과 정확히 일치하는지 확인

---

## 프로젝트별 규칙

### YOLO 모델 통합

- 모델 위치: `models/obstacle_detector/`, `models/product_recognizer/`
- 래퍼: `detectors/obstacle_dl.py`, `detectors/product_dl.py` (ultralytics v8+)
- `ObstacleDetector.detect()` 반환값: `{"danger_level": int, "objects": list}`
- `ProductRecognizer.recognize()` 반환값: `product_id` (DB 기본 키 매핑)

### UI 업데이트 (메인 허브 → PyQt6 대시보드)

UI 제어기는 **스레드 안전 업데이트를 위해 Qt 신호 사용**:
```python
# ui_controller.py에서
self.update_cart_signal.emit(cart_items)  # TCP 스레드에서 직접 UI 위젯 업데이트 금지
```

항상 신호를 발생시키고, 네트워크 스레드에서 대시보드 메서드를 직접 호출하지 마세요.

### 오류 처리

- **네트워크 작업**: TCP 클라이언트는 재시도/타임아웃 로직 포함
- **DB 작업**: DAOs는 오류 로깅만 수행 (반환값 확인)
- **YOLO 추론**: 추론 루프에서 예외 처리하여 스레드 충돌 방지

---

## 주요 파일

- [src/common/protocols.py](src/common/protocols.py) - 완전한 메시지 프로토콜 명세 + 열거형
- [src/core/engine.py](src/core/engine.py) - 한 곳에 모여 있는 모든 비즈니스 로직
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 상세 컴포넌트 문서
- [docs/QUICK_START_GUIDE.md](docs/QUICK_START_GUIDE.md) - 설치 단계 + 설정 예제
- [configs/network_config.yaml](configs/network_config.yaml) - 네트워크 토폴로지 참조

---

## 일반적인 함정

1. **프로토콜 불일치**: 항상 `protocols.py`의 열거형 값을 사용하고, 정수/문자열을 하드코딩하지 마세요
2. **스레드 안전성**: UI 업데이트는 Qt 신호, 공유 프레임 버퍼는 잠금 사용
3. **포트 충돌**: 컴포넌트가 연결할 수 없으면 `network_config.yaml` 확인
4. **모델 경로**: AI 서버 실행 전 `.pt` 파일이 `models/` 디렉토리에 있는지 확인
5. **DB 연결**: `.env.example`에서 `.env` 생성 후 `scripts/init_db.sql` 실행
