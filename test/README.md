# 🧪 테스트 디렉토리

## 📋 파일 설명

### 실행 스크립트
- **`run_hybrid_test.py`** - 1대 PC 하이브리드 테스트 (영상 파일 + 웹캠)
  - AI Server, Main Hub, Camera, UI를 모두 자동 실행
  - 전방 카메라: 영상 파일로 장애물 감지
  - 카트 카메라: 웹캠으로 상품 인식

### 카메라 앱
- **`optimized_hybrid_camera.py`** - 최적화된 하이브리드 카메라
  - 영상 파일(전방) + 웹캠(카트) 동시 실행
  - 실시간 디버깅 박스 표시
  - UDP로 프레임 전송

### 테스트 스크립트
- **`test_ui_update.py`** - UI UPDATE_CART 명령 테스트
  - DB에서 장바구니 데이터 조회
  - UI로 UPDATE_CART 메시지 전송

### 영상 파일
- **`Grocery Store Vocabulary_ shop in English.mp4`** - 전방 카메라용 테스트 영상

### 데이터 폴더
- **`yw/`** - 학습/추론 데이터 및 결과

---

## 🚀 빠른 시작

### 1. 전체 시스템 실행
```bash
cd /home/dh/dev_ws/git_ws/deeplearning-repo-1
python test/run_hybrid_test.py
```

### 2. 카메라만 실행
```bash
python test/optimized_hybrid_camera.py
```

### 3. UI 테스트
```bash
python test/test_ui_update.py
```

---

## 📚 상세 가이드

더 자세한 테스트 방법은 다음 문서를 참고하세요:
- [`docs/QUICK_START_GUIDE.md`](../docs/QUICK_START_GUIDE.md) - 빠른 시작 가이드
- [`docs/README_TEST_LOCAL.md`](../docs/README_TEST_LOCAL.md) - 로컬 테스트 가이드
- [`docs/E2E_TEST_GUIDE.md`](../docs/E2E_TEST_GUIDE.md) - End-to-End 테스트 가이드
