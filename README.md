# 🛒 AI 기반 지능형 쇼핑카트 시스템 (Smart Shopping Cart System)

이 프로젝트는 **YOLO 객체 인식** 기술과 **분산 컴퓨팅 아키텍처**를 결합하여, 실시간 장애물 감지 및 상품 자동 인식 기능을 제공하는 스마트 쇼핑카트 시스템입니다.

---

## 🏗️ 시스템 아키텍처 (System Architecture)

본 시스템은 실시간 연산 부하를 효율적으로 분산하고 각자의 역할에 집중하기 위해 3개의 독립적인 애플리케이션 노드로 구성됩니다.

1.  **AI 서버 (AI Inference Server):** 고성능 연산 자원을 활용하여 메인 허브로부터 전송받은 영상에서 장애물(사람, 기타 카트 등) 및 상품을 실시간으로 감지하고 분석합니다.
2.  **메인 허브 (Main Control Hub):** 시스템의 중앙 오케스트레이터입니다. 엣지 디바이스의 영상 데이터를 AI 서버로 중계하고, AI의 분석 결과를 받아 비즈니스 로직을 적용합니다. 또한, AWS RDS와 연동하여 세션 및 상품 데이터를 관리하고 UI에 필요한 정보를 전달합니다.
3.  **엣지 디바이스 (Edge Device - Shopping Cart):** 쇼핑카트에 장착된 클라이언트입니다.
    *   **카메라 앱:** 전방 및 카트 내부 카메라 영상을 메인 허브로 실시간 스트리밍합니다.
    *   **대시보드 UI:** PyQt6 기반의 GUI 애플리케이션으로, 사용자가 장바구니 내역과 총액, 장애물 경고 등 주요 정보를 확인할 수 있는 인터페이스를 제공합니다.

---

## 📂 디렉토리 구조 (Directory Structure)

```text
smart-shopping-cart/
├── src/
│   ├── main.py               # [메인 허브] 중앙 제어, 데이터 중계, 비즈니스 로직 실행
│   ├── ai_server.py          # [AI 서버] YOLO 추론 및 이벤트 생성
│   ├── cart_app.py           # [엣지] 카메라 영상 인코딩 및 UDP 전송 앱
│   ├── cart_ui_app.py        # [엣지] PyQt6 대시보드 UI 실행 앱
│   ├── core/
│   │   └── engine.py         # [핵심 로직] AI 이벤트 해석, DB 연동 등 비즈니스 로직 캡슐화
│   ├── network/
│   │   ├── tcp_server.py     # 제어 명령/이벤트 수신용 TCP 서버 래퍼
│   │   ├── tcp_client.py     # 제어 명령/이벤트 전송용 TCP 클라이언트 래퍼
│   │   └── udp_handler.py    # 실시간 영상 스트리밍용 UDP 핸들러
│   ├── database/
│   │   ├── db_handler.py     # DB 커넥션 및 CRUD 오퍼레이션 관리
│   │   ├── product_dao.py    # 상품(products) 테이블 접근 객체
│   │   ├── transaction_dao.py# 세션, 장바구니, 주문 등 트랜잭션 데이터 접근 객체
│   │   └── obstacle_log_dao.py # 장애물 감지 로그 데이터 접근 객체
│   ├── ui/
│   │   ├── dashboard.py      # PyQt6 대시보드 UI 레이아웃 정의
│   │   └── ui_controller.py  # UI 이벤트 처리 및 메인 허브와 통신
│   ├── detectors/
│   │   ├── obstacle_dl.py    # YOLO 장애물 탐지 모델 래퍼 클래스
│   │   └── product_dl.py     # YOLO 상품 인식 모델 래퍼 클래스
│   ├── common/
│   │   ├── config.py         # YAML 설정 파일을 로드하는 통합 설정 클래스
│   │   └── protocols.py      # 시스템 컴포넌트 간 통신 메시지 규격(Enum) 정의
│   └── utils/
│       ├── logger.py         # 시스템 전역 로깅 유틸리티
│       └── image_proc.py     # 이미지 처리 관련 유틸리티 함수
├── configs/                  # YAML 기반의 환경 설정 파일 디렉토리
│   ├── app_config.yaml       # 애플리케이션 관련 설정 (카메라 해상도 등)
│   ├── db_config.yaml        # 데이터베이스 연결 정보
│   ├── model_config.yaml     # AI 모델 경로 및 하이퍼파라미터
│   └── network_config.yaml   # IP, Port 등 네트워크 구성 정보
├── scripts/                  # DB 스키마(init_db.sql) 및 초기 데이터 스크립트
├── models/                   # 학습된 YOLOv5/v8 가중치(.pt) 파일
└── requirements.txt          # 프로젝트 의존성 라이브러리 목록
```

---

## 🚀 주요 기능 (Key Features)

### 1. 실시간 장애물 탐지 및 경고

-   **UDP Streaming:** 전방 카메라 영상을 JPEG로 압축하여 실시간으로 메인 허브에 전송합니다.
-   **Danger Level Analysis:** AI 서버가 객체의 종류, 크기, 거리를 분석하여 위험도를 판단하고, 위험 수준(`CAUTION` / `CRITICAL`)에 따라 UI에 시각적 경고를 표시합니다.

### 2. 상품 자동 스캔 및 장바구니 관리

-   **Automatic Recognition:** 카트 내부에 장착된 카메라가 카트에 담기는 상품을 자동으로 인식합니다.
-   **DB Integration:** AI 서버가 상품 ID를 전송하면, 메인 허브는 AWS RDS에서 실시간으로 가격 및 상품 정보를 조회하여 장바구니에 추가하고, 이 정보를 UI로 전송하여 동적으로 업데이트합니다.
-   **Duplicate Prevention:** `core/engine.py`에서 시간 기반의 중복 인식 방지 로직을 적용하여, 동일 상품이 짧은 시간 내에 여러 번 스캔되는 것을 방지합니다.

---

## 🛠️ 설치 및 실행 방법 (Installation & Usage)

### 1. 환경 설정

#### 필수 라이브러리 설치
모든 PC에서 필요한 라이브러리를 설치합니다.

```bash
pip install -r requirements.txt
```

#### 환경변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 데이터베이스 정보를 설정합니다.

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일 편집 (실제 DB 정보 입력)
# DB_HOST=your-rds-endpoint.ap-northeast-2.rds.amazonaws.com
# DB_PORT=3306
# DB_USER=root
# DB_PASSWORD=your-secure-password
# DB_NAME=smart_cart_db
```

⚠️ **중요:** `.env` 파일은 민감한 정보를 포함하므로 Git에 커밋하지 마세요. (`.gitignore`에 이미 추가되어 있음)

### 2. 인프라 준비

-   **데이터베이스:** `scripts/init_db.sql` 스크립트를 사용하여 DB 테이블을 생성합니다.
-   **초기 데이터:** `scripts/seed_data.py`를 실행하여 상품 마스터 데이터를 DB에 입력합니다.
-   **네트워크 설정:** `configs/network_config.yaml` 파일에서 각 PC의 IP 주소를 설정합니다. (로컬 테스트 시에는 모든 IP를 `127.0.0.1`로 설정)

### 3. 시스템 가동 (권장 순서)

각 컴포넌트를 별도의 터미널에서 실행합니다.

1.  **AI 서버 (PC1):**
    ```bash
    python src/ai_server.py
    ```
2.  **메인 허브 (PC2):**
    ```bash
    python src/main.py
    ```
3.  **카트 UI (PC3):**
    ```bash
    python src/cart_ui_app.py
    ```
4.  **카트 카메라 앱 (PC3):**
    ```bash
    python src/cart_app.py
    ```

---

## 📡 데이터 통신 규격 (Communication Protocol)

모든 컴포넌트 간의 통신은 `src/common/protocols.py`에 정의된 `Protocol` 클래스를 따르며, 메시지는 JSON 형식으로 구성됩니다.

| 메시지 타입 | 송신자           | 수신자           | 설명                                                                                                                                                                          |
| :---------- | :--------------- | :--------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AI_EVT`    | AI 서버          | 메인 허브        | AI가 장애물 또는 상품을 감지했을 때 발생하는 이벤트. 감지된 객체의 정보(위험도, 상품 ID 등)를 포함하여 메인 허브로 푸시(Push)됩니다.                                                   |
| `UI_CMD`    | 메인 허브        | UI 대시보드      | 메인 허브가 UI를 제어하기 위한 명령입니다. 알람 표시, 장바구니에 상품 추가/갱신, 결제 완료 알림 등의 역할을 합니다.                                                              |
| `UI_REQ`    | UI 대시보드      | 메인 허브        | UI에서 사용자 요청(예: 쇼핑 세션 시작, 결제 진행)이 발생했을 때 메인 허브로 전송하는 메시지입니다.                                                                         |
| `AI_REQ`    | (현재 미사용) | (현재 미사용) | AI 서버에 특정 분석을 요청하는 메시지입니다. (예: 특정 프레임에 대한 즉각적인 분석 요청)                                                                                                    |
| `AI_RES`    | (현재 미사용) | (현재 미사용) | `AI_REQ`에 대한 AI 서버의 응답 메시지입니다. 분석 결과 또는 오류 정보를 포함합니다.                                                                                                       |

---

## 📖 프로토콜 Enums 상세 (Protocol Enums Details)

`src/common/protocols.py` 파일에 정의된 Enum들은 시스템의 다양한 메시지 타입과 이벤트, 명령의 구체적인 유형을 정의합니다.

### `MessageType`
시스템 내에서 사용되는 메시지의 상위 분류를 정의합니다.
- `AI_REQ = 1`: AI 요청
- `AI_RES = 2`: AI 응답
- `AI_EVT = 3`: AI 이벤트
- `UI_REQ = 10`: UI 요청
- `UI_CMD = 11`: UI 명령
- `UI_EVT = 12`: UI 이벤트
- `DB_REQ = 20`: DB 요청
- `DB_RES = 21`: DB 응답

### `AITask`
AI 서버에 요청할 특정 분석 태스크의 종류를 정의합니다.
- `OBSTACLE = 1`: 장애물 관련 태스크
- `PRODUCT = 2`: 상품 관련 태스크

### `UICommand` (메인 허브 -> UI 대시보드)
메인 허브가 UI 대시보드에 특정 동작을 지시할 때 사용하는 명령 유형을 정의합니다.
- `SHOW_ALARM = 1`: UI에 알람 표시
- `ADD_TO_CART = 2`: 장바구니에 상품 추가
- `UPDATE_STATUS = 3`: UI의 상태 업데이트
- `CHECKOUT_DONE = 4`: 결제 완료 알림

### `UIRequest` (UI 대시보드 -> 메인 허브)
UI 대시보드에서 메인 허브로 사용자 요청을 보낼 때 사용하는 요청 유형을 정의합니다.
- `START_SESSION = 1`: 새로운 쇼핑 세션 시작 요청
- `CHECKOUT = 2`: 현재 장바구니 결제 요청

### `DBAction` (메인 허브 -> DB)
메인 허브가 데이터베이스에 수행할 동작의 종류를 정의합니다.
- `GET_PRODUCT = 1`: 상품 정보 조회
- `ADD_CART_ITEM = 2`: 장바구니에 상품 추가
- `GET_CART = 3`: 장바구니 내용 조회

### `AIEvent` (AI 서버 -> 메인 허브)
AI 서버에서 감지된 특정 이벤트의 종류를 정의합니다.
- `OBSTACLE_DANGER = 1`: 장애물 위험 감지
- `PRODUCT_DETECTED = 2`: 상품 감지

### `DangerLevel`
장애물 감지 시 위험 수준을 나타내는 등급을 정의합니다.
- `NORMAL = 0`: 정상
- `CAUTION = 1`: 주의
- `CRITICAL = 2`: 위험