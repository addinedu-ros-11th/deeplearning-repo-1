# AI Smart Cart - GUI 화면 구성도

## 개요
AI Smart Cart의 사용자 인터페이스는 3가지 주요 상태로 구성되며, 상태 간 전환을 통해 쇼핑 프로세스를 관리합니다.

## 화면 상태 (Screen States)

### 1. 대기 화면 (STANDBY State)
**목적:** 카트 사용 시작 전 초기 화면

```
┌────────────────────────────────────────────────────────────┐
│              AI Smart Cart Dashboard                       │
│                                                            │
│                                                            │
│                        🛒                                  │
│                                                            │
│              AI Smart Cart Ready                           │
│                                                            │
│          Tap 'Start Shopping' to begin                     │
│                                                            │
│                                                            │
│            ┌──────────────────────┐                        │
│            │  🛍️  Start Shopping  │                        │
│            └──────────────────────┘                        │
│                                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**구성 요소:**
- 카트 아이콘 (🛒) - 120pt
- 제목: "AI Smart Cart Ready" - 32pt, Bold
- 부제목: "Tap 'Start Shopping' to begin" - 18pt, Gray
- 버튼: "Start Shopping" - 300x70px, 초록색 (#4CAF50)

**동작:**
- "Start Shopping" 클릭 → Main Hub에 START_SESSION 요청 → SHOPPING 상태로 전환

---

### 2. 쇼핑 화면 (SHOPPING State)
**목적:** 실시간 장바구니 관리 및 상품/장애물 모니터링

```
┌────────────────────────────────────────────────────────────────────────────┐
│  🛒 Shopping in Progress              ⏱️ Shopping Time: 00:05:32          │
├────────────────────────────────────────┬───────────────────────────────────┤
│                                        │                                   │
│  📦 Cart Items                         │   ⚠️ Obstacle Status             │
│  ┌──────────────────────────────────┐ │         ┌─────┐                  │
│  │ Product    │ Price  │ Qty │ Sub  │ │         │ 🟢  │                  │
│  ├──────────────────────────────────┤ │         └─────┘                  │
│  │ Yukgaejang │ ₩1200  │  2  │₩2400│ │       No Obstacles                │
│  │ Coke       │ ₩1500  │  1  │₩1500│ │                                   │
│  │ Chips      │ ₩2000  │  3  │₩6000│ │                                   │
│  │            │        │     │      │ │                                   │
│  │            │        │     │      │ │                                   │
│  └──────────────────────────────────┘ │   💰 Total Amount                │
│                                        │                                   │
│                                        │       ₩ 9,900                    │
│                                        │                                   │
│                                        │       3 items                     │
│                                        │                                   │
│                                        │                                   │
│                                        │                                   │
│                          ┌─────────────────────┐                          │
│                          │  🏁 Finish Shopping │                          │
│                          └─────────────────────┘                          │
└────────────────────────────────────────────────────────────────────────────┘

                Toast Notification (3초간 표시)
                ┌────────────────────────────┐
                │ ✅ Yukgaejang added to cart!│
                └────────────────────────────┘
```

**구성 요소:**

#### 헤더 영역
- 제목: "🛒 Shopping in Progress" - 24pt, Bold
- 쇼핑 타이머: "⏱️ Shopping Time: HH:MM:SS" - 14pt, 파란색

#### 메인 영역 (좌측 - 장바구니 테이블)
- 제목: "📦 Cart Items" - 16pt, Bold
- 테이블 컬럼:
  - Product (상품명)
  - Price (가격)
  - Qty (수량)
  - Subtotal (소계)
- 교차 행 색상 적용
- 스크롤 가능

#### 메인 영역 (우측 - 정보 패널)
1. **장애물 상태 표시**
   - 제목: "⚠️ Obstacle Status" - 14pt, Bold
   - LED 인디케이터: 80x80px, 원형
     - 🟢 초록색: 안전 (DangerLevel.NORMAL)
     - 🟡 노란색: 주의 (DangerLevel.CAUTION)
     - 🔴 빨간색: 위험 (DangerLevel.CRITICAL)
   - 상태 텍스트: 동적 메시지 표시

2. **총액 표시**
   - 제목: "💰 Total Amount" - 14pt, Bold
   - 금액: "₩ XXX,XXX" - 28pt, Bold, 초록색
   - 아이템 수: "X items" - 12pt, Gray

#### 하단 영역
- 버튼: "🏁 Finish Shopping" - 200x50px, 주황색 (#FF5722)

#### 알림 (Toast Notification)
- 위치: 하단 중앙
- 크기: 자동 조정
- 배경: 반투명 초록색 (rgba(76, 175, 80, 220))
- 텍스트: "✅ {상품명} added to cart!" - 16pt, Bold, 흰색
- 애니메이션: 페이드 인/아웃 (300ms)
- 표시 시간: 3초

**동작:**
- 상품 인식 → UPDATE_CART 명령 수신 → 테이블 업데이트 + Toast 표시
- 장애물 감지 → SHOW_ALARM 명령 수신 → LED 색상 변경 + 메시지 업데이트
- "Finish Shopping" 클릭 → 체크아웃 확인 다이얼로그 표시

---

### 3. 체크아웃 확인 다이얼로그 (Checkout Dialog)
**목적:** 구매 확정 전 최종 확인

```
        ┌─────────────────────────────────────┐
        │  Checkout Confirmation              │
        │                                     │
        │    🛒 Complete Your Shopping?       │
        │                                     │
        │                                     │
        │    Total Amount: ₩ 9,900           │
        │                                     │
        │                                     │
        │  ┌───────────┐    ┌───────────┐   │
        │  │ ❌ Cancel  │    │ ✅ Confirm │   │
        │  └───────────┘    └───────────┘   │
        │                                     │
        └─────────────────────────────────────┘
```

**구성 요소:**
- 크기: 450x250px, 모달
- 제목: "🛒 Complete Your Shopping?" - 20pt, Bold
- 총액: "Total Amount: ₩ XXX,XXX" - 24pt, Bold, 파란색
- 버튼:
  - Cancel: 회색 (#757575), 50px 높이
  - Confirm: 초록색 (#4CAF50), 50px 높이

**동작:**
- Cancel 클릭 → 다이얼로그 닫기, 쇼핑 계속
- Confirm 클릭 → Main Hub에 CHECKOUT 요청 → STANDBY 상태로 복귀

---

## 상태 전환 다이어그램

```
    ┌──────────┐
    │ STANDBY  │
    └─────┬────┘
          │ [Start Shopping 클릭]
          │ → START_SESSION 요청
          ↓
    ┌──────────┐
    │ SHOPPING │←─────────┐
    └─────┬────┘          │
          │               │ [Cancel 클릭]
          │ [Finish Shopping 클릭]
          ↓               │
    ┌──────────────┐      │
    │ Checkout     │──────┘
    │ Dialog       │
    └─────┬────────┘
          │ [Confirm 클릭]
          │ → CHECKOUT 요청
          ↓
    ┌──────────┐
    │ STANDBY  │
    └──────────┘
```

---

## 컴포넌트 상세

### 1. LEDWidget (장애물 표시 LED)
- **타입:** 커스텀 QFrame
- **크기:** 80x80px (기본값, 조정 가능)
- **모양:** 원형 (border-radius: 50%)
- **색상:**
  - NORMAL: #4CAF50 (초록)
  - CAUTION: #FFC107 (노랑)
  - CRITICAL: #F44336 (빨강)
- **테두리:** 3px solid #ddd

### 2. ToastNotification (알림 토스트)
- **타입:** 커스텀 QWidget (FramelessWindowHint)
- **배경:** rgba(76, 175, 80, 220) - 반투명 초록
- **패딩:** 15px 25px
- **border-radius:** 10px
- **폰트:** 16pt, Bold, 흰색
- **애니메이션:**
  - Fade In: 300ms, InOutQuad easing
  - Fade Out: 300ms (3초 후)
- **위치:** 부모 하단 중앙 (bottom - 50px)

### 3. CheckoutDialog (체크아웃 다이얼로그)
- **타입:** QDialog (Modal)
- **크기:** 450x250px (고정)
- **구성:**
  - 제목 영역: 20pt, Bold
  - 금액 영역: 24pt, Bold, 파란색
  - 버튼 영역: 높이 50px, 간격 포함

### 4. CartTable (장바구니 테이블)
- **타입:** QTableWidget
- **컬럼:** 4개 (Product, Price, Qty, Subtotal)
- **설정:**
  - 편집 불가 (NoEditTriggers)
  - 교차 행 색상 (AlternatingRowColors)
  - 마지막 컬럼 자동 확장 (StretchLastSection)
- **기본 컬럼 너비:** 150px
- **정렬:** 최근 추가 순 (added_at DESC)

---

## 색상 팔레트

### 주요 색상
- **Primary Green (성공/확인):** #4CAF50
- **Primary Blue (정보):** #2196F3
- **Warning Orange:** #FF5722
- **Danger Red:** #F44336
- **Caution Yellow:** #FFC107

### 보조 색상
- **Gray (비활성/보조):** #757575
- **Light Gray (테두리):** #ddd
- **White (텍스트/배경):** #ffffff

### 토스트 배경
- **Success Toast:** rgba(76, 175, 80, 220)

---

## 폰트 가이드

### 제목
- **메인 제목:** Arial, 32pt, Bold
- **서브 제목:** Arial, 24pt, Bold
- **섹션 제목:** Arial, 16pt, Bold
- **소제목:** Arial, 14pt, Bold

### 본문
- **일반 텍스트:** Arial, 12pt, Regular
- **강조 텍스트:** Arial, 14pt, Regular/Bold
- **금액 표시:** Arial, 28pt, Bold

### 버튼
- **대형 버튼:** Arial, 20pt, Bold
- **중형 버튼:** Arial, 16pt, Bold
- **소형 버튼:** Arial, 14pt, Bold

---

## 레이아웃 크기

### 메인 윈도우
- **크기:** 1024x768px (고정)
- **제목:** "AI Smart Cart Dashboard"

### 쇼핑 화면 비율
- **좌측 (장바구니):** 75% (약 768px)
- **우측 (정보 패널):** 25% (약 256px)

### 버튼 크기
- **대형 (Start Shopping):** 300x70px
- **중형 (Finish Shopping):** 200x50px
- **소형 (Dialog 버튼):** 자동 너비 x 50px

---

## 실시간 업데이트 흐름

### 상품 추가 시퀀스
```
1. AI Server: 상품 인식
   ↓
2. Main Hub: DB에 저장 (cart_items)
   ↓
3. Main Hub → UI: UPDATE_CART 명령 전송
   ↓
4. UI Controller: 메시지 수신
   ↓
5. Dashboard: 테이블 업데이트
   ↓
6. Dashboard: Toast 알림 표시 (3초)
```

### 장애물 감지 시퀀스
```
1. AI Server: 장애물 감지
   ↓
2. Main Hub: 위험도 계산
   ↓
3. Main Hub → UI: SHOW_ALARM 명령 전송
   ↓
4. UI Controller: 메시지 수신
   ↓
5. Dashboard: LED 색상 변경
   ↓
6. Dashboard: 상태 텍스트 업데이트
   ↓
7. UI Controller: DB에 로그 저장 (obstacle_logs)
```

---

## 반응형 동작

### 테이블 스크롤
- 5개 이상 항목 시 자동 스크롤바 표시
- 마우스 휠 스크롤 지원

### 버튼 호버 효과
- Start Shopping: #4CAF50 → #45a049
- Finish Shopping: #FF5722 → #E64A19
- Cancel: #757575 → #616161
- Confirm: #4CAF50 → #45a049

### 애니메이션
- **토스트 페이드:** 300ms easing curve
- **LED 색상 전환:** 즉시 (0ms)
- **다이얼로그 표시:** 시스템 기본

---

## 접근성 고려사항

### 색상 대비
- 모든 텍스트는 배경과 4.5:1 이상의 명암비 유지
- LED 색상은 문자 메시지로도 상태 표시

### 폰트 크기
- 최소 12pt 이상 사용
- 중요 정보는 16pt 이상

### 명확한 피드백
- 모든 버튼 클릭에 즉각적인 피드백
- 토스트 알림으로 액션 결과 확인

---

## 기술 스택

- **UI Framework:** PyQt6
- **레이아웃:** QVBoxLayout, QHBoxLayout
- **상태 관리:** QStackedWidget (3 pages)
- **애니메이션:** QPropertyAnimation (opacity)
- **시그널/슬롯:** PyQt6 signals for thread-safe updates
- **스타일:** QSS (Qt Style Sheets)

---

## 파일 구조

```
src/ui/
├── dashboard_v2.py         # 메인 UI 클래스 (CartDashboard)
│   ├── LEDWidget          # LED 인디케이터
│   ├── ToastNotification  # 알림 토스트
│   ├── CheckoutDialog     # 체크아웃 다이얼로그
│   └── CartDashboard      # 메인 대시보드
│
└── ui_controller_v2.py     # UI 컨트롤러 (비즈니스 로직)
    ├── UIEventSignals     # Qt 시그널 정의
    └── UIController       # 메인 컨트롤러

src/cart_ui_app_v2.py       # 애플리케이션 엔트리포인트
```

---

## 향후 개선 사항

### UI/UX 개선
- [ ] 다크 모드 지원
- [ ] 다국어 지원 (한국어/영어)
- [ ] 터치스크린 최적화 (버튼 크기 조정)
- [ ] 음성 피드백 추가

### 기능 추가
- [ ] 장바구니 아이템 개별 삭제 기능
- [ ] 수량 직접 조정 기능
- [ ] 쿠폰/할인 적용 UI
- [ ] 이전 주문 내역 조회

### 성능 최적화
- [ ] 테이블 가상 스크롤 (대량 아이템)
- [ ] 이미지 캐싱 (상품 썸네일)
- [ ] 애니메이션 프레임 제한

---

## 참고 자료

- PyQt6 공식 문서: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- Qt Style Sheets: https://doc.qt.io/qt-6/stylesheet.html
- Material Design Colors: https://material.io/design/color/
