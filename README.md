# 스마트 카트 (Smart Cart) 프로젝트

YOLO 기반 상품 및 장애물 인식을 활용한 스마트 쇼핑 카트 시스템

## 프로젝트 개요

이 프로젝트는 딥러닝 기반의 객체 인식 기술을 활용하여 쇼핑 카트에 담긴 상품을 자동으로 인식하고, 주변 장애물을 감지하여 사용자에게 안전한 쇼핑 경험을 제공하는 시스템입니다.

### 주요 기능

- **상품 자동 인식**: YOLO 모델을 사용하여 아이스크림, 과자, 라면 등 9가지 상품 자동 인식
- **품질 검사**: 상품의 외관 손상 여부를 자동으로 감지
- **장애물 감지**: 사람 및 다른 카트를 실시간으로 감지하여 충돌 방지
- **실시간 모니터링**: 카트 내 상품 목록과 총 금액을 실시간으로 표시
- **이벤트 로깅**: 모든 상품 인식 및 장애물 감지 이벤트 기록
- **구매 관리**: 구매 완료 시 데이터 저장 및 관리

## 시스템 요구사항

### 하드웨어
- 노트북 2대 (각각 내장 카메라 포함)
  - 1번 노트북: 상품 인식용 (캠1)
  - 2번 노트북: 장애물 인식용 (캠2)

### 소프트웨어
- Python 3.8 이상
- CUDA 지원 GPU (권장)
- AWS RDS MySQL 데이터베이스

## 프로젝트 구조

```
deeplearning-repo-1/
├── config/                      # 설정 파일
│   ├── config.yaml             # 시스템 설정
│   ├── config.py               # 설정 로더
│   └── db_config.py            # 데이터베이스 설정
│
├── models/                      # YOLO 모델 파일
│   ├── product_yolo/           # 상품 인식 모델
│   │   ├── icecream.pt         # 아이스크림 인식 모델
│   │   ├── snack.pt            # 과자 인식 모델
│   │   └── ramen.pt            # 라면 인식 모델
│   └── obstacle_yolo/          # 장애물 인식 모델
│       ├── person.pt           # 사람 인식 모델
│       └── cart.pt             # 카트 인식 모델
│
├── database/                    # 데이터베이스 계층
│   ├── db_manager.py           # DB 연결 및 ORM 모델
│   ├── product_repository.py   # 상품 데이터 관리
│   ├── cart_repository.py      # 카트 데이터 관리
│   ├── log_repository.py       # 로그 데이터 관리
│   └── purchase_repository.py  # 구매 데이터 관리
│
├── detection/                   # 객체 인식 모듈
│   ├── product_detector.py     # 상품 인식
│   ├── obstacle_detector.py    # 장애물 인식
│   ├── quality_inspector.py    # 품질 검사
│   └── utils.py                # 인식 유틸리티
│
├── server/                      # 서버 모듈
│   ├── tcp_server.py           # TCP 서버
│   ├── udp_server.py           # UDP 서버 (실시간 스트리밍)
│   └── message_handler.py      # 메시지 처리
│
├── client/                      # 클라이언트 모듈
│   ├── product_recognition_client.py   # 상품 인식 클라이언트 (캠1)
│   └── obstacle_recognition_client.py  # 장애물 인식 클라이언트 (캠2)
│
├── business_logic/              # 비즈니스 로직
│   ├── cart_manager.py         # 카트 관리
│   ├── product_manager.py      # 상품 관리
│   ├── obstacle_manager.py     # 장애물 관리
│   ├── alarm_manager.py        # 알람 관리
│   └── purchase_manager.py     # 구매 관리
│
├── gui/                         # GUI 인터페이스
│   ├── user_ui.py              # 사용자 UI (카트 화면)
│   ├── admin_ui.py             # 관리자 UI (모니터링)
│   └── ui_components/          # UI 컴포넌트
│
├── utils/                       # 유틸리티
│   ├── logger.py               # 로깅
│   ├── image_utils.py          # 이미지 처리
│   └── network_utils.py        # 네트워크 유틸리티
│
├── logs/                        # 로그 파일 저장소
├── main.py                      # 메인 실행 파일
├── requirements.txt             # 의존성 패키지
└── README.md                    # 프로젝트 문서
```

## 설치 방법

### 1. 저장소 클론
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
```

### 2. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 설정
`config/config.yaml` 파일에서 AWS RDS MySQL 정보를 설정합니다

### 4. YOLO 모델 배치
학습된 YOLO 모델 파일을 `models/` 디렉토리에 배치합니다

## 실행 방법

### 시스템 구동 순서

1. **서버 실행**: `python main.py server`
2. **상품 인식 클라이언트** (1번 노트북): `python main.py product-client --host <서버_IP>`
3. **장애물 인식 클라이언트** (2번 노트북): `python main.py obstacle-client --host <서버_IP>`
4. **사용자 UI**: `python main.py user-ui --host <서버_IP>`
5. **관리자 UI**: `python main.py admin-ui --host <서버_IP>`

## 시스템 동작 방식

### 계층 구조
1. **프레젠테이션 계층**: GUI (사용자 UI, 관리자 UI)
2. **애플리케이션 계층**: 클라이언트 (상품/장애물 인식)
3. **비즈니스 로직 계층**: 매니저 클래스들 (카트, 상품, 장애물 관리)
4. **데이터 액세스 계층**: Repository 패턴
5. **인프라 계층**: 서버 (TCP/UDP), 데이터베이스

### 동작 흐름

#### 1. 쇼핑 시작
- 사용자 UI에서 "쇼핑 시작" → 서버에 TCP 요청 → 고유 세션 ID 생성 → DB에 카트 생성

#### 2. 상품 인식 (캠1 - 상품 인식 노트북)
- 카메라 프레임 캡처 → YOLO 모델 (아이스크림/과자/라면) 인식 → 품질 검사 모듈 실행
- 손상 여부 판단 → 정상 상품만 UDP로 서버 전송 → 서버가 DB에 저장 → 사용자 UI 업데이트

#### 3. 장애물 감지 (캠2 - 장애물 인식 노트북)
- 카메라 프레임 캡처 → YOLO 모델 (사람/카트) 인식 → 거리/방향/속도 계산
- 충돌 위험도 판단 → UDP로 서버 전송 → 위험 시 알람 매니저 작동 → 사용자에게 경고

#### 4. 구매 완료
- 사용자 UI에서 "구매 완료" → TCP로 서버에 요청 → 최종 카트 정보 조회
- Purchase 테이블에 저장 → 카트 상태 'completed'로 변경 → 이벤트 로그 기록

#### 5. 관리자 모니터링
- 5초마다 자동 새로고침 → 활성 카트, 장애물 감지 현황, 구매 이력, 이벤트 로그 조회

## 네트워크 구조

### TCP (포트 5000)
- **용도**: 제어 명령 및 상태 관리
- **메시지 타입**:
  - `cart_start`: 쇼핑 시작
  - `cart_end`: 쇼핑 종료
  - `product_add`: 상품 추가
  - `product_remove`: 상품 제거
  - `get_cart_info`: 카트 정보 조회
  - `purchase_complete`: 구매 완료

### UDP (포트 5001)
- **용도**: 실시간 데이터 스트리밍 (저지연)
- **메시지 타입**:
  - `product_detection`: 상품 인식 결과
  - `obstacle_detection`: 장애물 감지 결과

## 데이터베이스 구조

### 주요 테이블
- **products**: 상품 마스터 데이터 (이름, 카테고리, 가격, 이미지)
- **carts**: 카트 세션 (세션 ID, 상태, 생성/수정 시간)
- **cart_items**: 카트 내 상품 (카트 ID, 상품 ID, 수량, 가격, 손상 여부)
- **event_logs**: 이벤트 로그 (세션 ID, 이벤트 타입, 데이터, 시간)
- **obstacle_logs**: 장애물 로그 (세션 ID, 유형, 거리, 방향, 속도, 경고 레벨)
- **purchases**: 구매 정보 (세션 ID, 총액, 결제 방법, 이미지)
- **purchase_items**: 구매 상품 (구매 ID, 상품 ID, 수량, 가격)

## 폴더별 역할 설명

### `/config`
시스템 전체 설정 관리. YAML 파일로 서버, 카메라, DB, YOLO 모델 경로 등을 설정

### `/models`
학습된 YOLO 모델 파일 저장. 카테고리별로 나뉜 모델 사용

### `/database`
데이터베이스 접근 계층. Repository 패턴으로 각 테이블별 CRUD 작업 관리

### `/detection`
YOLO 기반 객체 인식 모듈. 상품 인식, 장애물 감지, 품질 검사 기능 제공

### `/server`
TCP/UDP 서버 구현. 메시지 핸들러가 비즈니스 로직과 연결

### `/client`
2대의 노트북에서 실행. 각각 상품/장애물 인식 담당

### `/business_logic`
핵심 비즈니스 로직. 카트, 상품, 장애물, 알람, 구매 관리

### `/gui`
PyQt5 기반 사용자/관리자 인터페이스

### `/utils`
공통 유틸리티 (로깅, 이미지 처리, 네트워크)

## 개발 정보

- **기술 스택**: Python 3.8+, YOLOv8, PyQt5, SQLAlchemy, OpenCV
- **데이터베이스**: AWS RDS MySQL
- **통신**: TCP/UDP Socket Programming
- **아키텍처**: 계층형 아키텍처 (Layered Architecture)
- **디자인 패턴**: Repository Pattern, Singleton Pattern
