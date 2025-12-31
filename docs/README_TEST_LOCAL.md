# PC 1대로 테스트하기

## ✅ 현재 상태
- 설정 파일 수정 완료 (모든 IP를 127.0.0.1로 설정)
- 모델 경로 수정 완료 (dummy.pt, product_yolo8s.pt 사용)
- AI Server가 정상 실행됨

## 🚀 실행 방법

### 방법 1: 자동 실행 스크립트 (권장)
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
/home/dh/venv/yolo/bin/python test/run_all_local.py
```

### 방법 2: 수동으로 터미널 4개 사용

#### Terminal 1: AI Server
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
/home/dh/venv/yolo/bin/python src/ai_server.py
```
예상 출력:
```
Initializing AI Server...
Loading obstacle detection model...
Loading product recognition model...
UDP receivers listening on ports 5000 and 5001
Event client configured to connect to 127.0.0.1:6002
Obstacle UDP loop started.
Product UDP loop started.
Obstacle inference loop started.
Product inference loop started.
```

#### Terminal 2: Main Hub
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
/home/dh/venv/yolo/bin/python src/main_hub.py
```

#### Terminal 3: 카메라 앱
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
/home/dh/venv/yolo/bin/python src/cart_camera_app.py
```
**주의**: 웹캠이 2대 필요합니다. 없으면 에러 발생!

#### Terminal 4: UI 앱
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
/home/dh/venv/yolo/bin/python src/cart_ui_app.py
```

## 📹 웹캠이 없는 경우

테스트 영상 파일을 사용하세요:

```bash
# Terminal 3-1: 전방 카메라 시뮬레이션
python test/video_streamer.py test/yw/data/raw/test_video.mp4 \
    --host 127.0.0.1 --port 6000 --fps 30

# Terminal 3-2: 카트 카메라 시뮬레이션  
python test/video_streamer.py test/yw/data/raw/test_video.mp4 \
    --host 127.0.0.1 --port 6001 --fps 30
```

## 🔍 동작 확인

1. **AI Server**: 모델 로딩 완료 메시지 확인
2. **Main Hub**: 세션 시작 메시지 확인
3. **Camera App**: 스트리밍 시작 메시지 확인
4. **UI App**: PyQt6 창이 열림

## ⚠️ 주의사항

### 1. 데이터베이스 연결
현재 `configs/db_config.yaml`의 DB 정보를 확인하세요:
```yaml
aws_rds:
  host: "your-rds-endpoint.aws.com"  # 실제 DB 주소로 변경 필요
  port: 3306
  user: "admin"
  password: "your_password_here"      # 실제 비밀번호로 변경 필요
  database: "smart_cart_db"
```

**DB 없이 테스트**하려면 main_hub.py 실행 시 에러가 발생할 수 있습니다.

### 2. 포트 충돌
다음 포트들이 이미 사용 중이면 에러 발생:
- 5000, 5001 (AI Server UDP)
- 6000, 6001 (Main Hub UDP)
- 6002 (Main Hub TCP - AI 이벤트)
- 7000 (Main Hub TCP - UI 요청)
- 7001 (UI TCP - 명령 수신)

확인 방법:
```bash
netstat -tuln | grep -E '(5000|5001|6000|6001|6002|7000|7001)'
```

## 🐛 문제 해결

### AI Server가 시작되지 않음
```bash
# 모델 파일 확인
ls -lh models/obstacle_detector/
ls -lh models/product_recognizer/
```

### Main Hub가 시작되지 않음
- DB 연결 실패일 가능성
- `configs/db_config.yaml` 확인

### Camera App이 시작되지 않음
- 웹캠 장치 확인: `ls -l /dev/video*`
- 영상 스트리머 사용 권장

### UI App이 보이지 않음
- DISPLAY 환경변수 확인
- X11 forwarding 필요 (SSH 접속 시)

## 📊 로그 확인

```bash
# 로그 디렉토리 생성
mkdir -p logs

# 로그를 파일로 저장하며 실행
/home/dh/venv/yolo/bin/python src/ai_server.py 2>&1 | tee logs/ai_server.log
```

## 🎯 다음 단계

시스템이 정상 실행되면:

1. **UI에서 "Start Shopping" 버튼 클릭**
2. **카메라에 물체를 비추기**
   - 전방 카메라: 사람 또는 장애물
   - 카트 카메라: 상품
3. **UI에서 결과 확인**
   - 장애물 경고
   - 장바구니 아이템 추가
4. **"Checkout" 버튼으로 주문 완료**

## 🔧 현재 설정 요약

| 컴포넌트 | IP | 포트 | 상태 |
|---------|-----|------|------|
| AI Server | 127.0.0.1 | UDP 5000, 5001 | ✅ 정상 |
| Main Hub | 127.0.0.1 | TCP 6002, 7000<br>UDP 6000, 6001 | 🔄 DB 필요 |
| Camera App | 127.0.0.1 | → 6000, 6001 | ⚠️ 웹캠 필요 |
| UI App | 127.0.0.1 | TCP 7001 | ✅ 정상 예상 |

## 📝 간단 테스트 명령

```bash
# 네트워크 통신만 테스트 (DB/모델 불필요)
/home/dh/venv/yolo/bin/python test/test_local_simple.py

# 전체 시스템 실행
/home/dh/venv/yolo/bin/python test/run_all_local.py
```
