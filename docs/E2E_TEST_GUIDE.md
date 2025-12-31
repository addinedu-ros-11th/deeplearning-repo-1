# E2E 상품 인식 → DB → UI 테스트 가이드

## 현재 실행 중인 시스템

### 실행 중인 프로세스:
- **AI Server** (PID: ai_server.log)
- **Main Hub** (PID: main_hub.log) - 세션 ID: 11
- **Hybrid Camera** - 웹캠 + 영상 파일
- **UI App** - 장바구니 대시보드

## 테스트 흐름

### 1. 상품 인식 (Camera → AI Server)
```
웹캠에 물건 보여주기
→ YOLO 모델이 class_id 검출 (예: class 1)
→ AI Server에 PRODUCT 이벤트 전송
```

### 2. DB 저장 (AI Server → Main Hub → DB)
```
Main Hub가 PRODUCT 이벤트 수신
→ engine.process_product_event() 호출
→ ProductDAO.get_product_by_id(1) - DB에서 상품 정보 조회
→ TransactionDAO.add_cart_item(session_id=11, product_id=1)
```

### 3. 장바구니 업데이트 (DB → Main Hub → UI)
```
TransactionDAO.list_cart_items(session_id=11) 호출
→ JOIN으로 상품 정보 가져오기:
  {
    product_id: 1,
    product_name: "Mountain Dew",
    price: 2500,
    quantity: 1,
    subtotal: 2500
  }
→ Protocol.ui_command(UPDATE_CART, {items: [...], total: 2500})
→ UI가 cart_updated 시그널 emit
→ dashboard.update_cart_display() 호출
→ QTableWidget 업데이트
```

## 데이터베이스 상태

### products 테이블:
| product_id | name | price | category_id |
|------------|------|-------|-------------|
| 1 | Mountain Dew | 2500 | 1 |
| 2 | Monster Energy | 3000 | 1 |
| 3 | Pocari Sweat | 1800 | 1 |
| 4 | Banana Kick | 1500 | 2 |
| ... | ... | ... | ... |

### shopping_sessions:
| session_id | cart_id | status | start_time |
|------------|---------|--------|------------|
| 11 | 1 | ACTIVE | 2025-01-XX |

### cart_items (실시간 추가됨):
| item_id | session_id | product_id | quantity | added_at |
|---------|------------|------------|----------|----------|
| (자동) | 11 | X | Y | (now) |

## UI 업데이트 로직

### UIController.py
```python
# UPDATE_CART 커맨드 수신
if cmd == UICommand.UPDATE_CART:
    items = payload["content"]["items"]  # [{product_name, price, quantity, subtotal}, ...]
    total = payload["content"]["total"]   # 총합
    self.signals.cart_updated.emit(items, total)
```

### CartDashboard.py
```python
def update_cart_display(self, items: list, total: float):
    # 테이블 클리어
    self.table.setRowCount(0)
    
    # 각 상품을 테이블에 추가
    for item in items:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(item["product_name"]))
        self.table.setItem(row, 1, QTableWidgetItem(f"₩ {item['price']}"))
        self.table.setItem(row, 2, QTableWidgetItem(str(item["quantity"])))
    
    # 총액 업데이트
    self.total_label.setText(f"₩ {int(total)}")
```

## 테스트 방법

### 1. 현재 세션 확인
```bash
mysql -h database-1.chu0kq8imwi9.ap-northeast-2.rds.amazonaws.com -u root -p'Q!w2e3r4t5' smart_cart_db \
  -e "SELECT * FROM shopping_sessions WHERE status='ACTIVE';"
```

### 2. 장바구니 비우기 (필요시)
```bash
mysql -h database-1.chu0kq8imwi9.ap-northeast-2.rds.amazonaws.com -u root -p'Q!w2e3r4t5' smart_cart_db \
  -e "DELETE FROM cart_items WHERE session_id=11;"
```

### 3. 상품 인식 테스트
1. Cart Camera 창에 물건을 가져다 대기
2. 녹색 바운딩 박스가 나타나는지 확인 (예: "ID:1 0.95")
3. UI 장바구니에 상품이 추가되는지 확인
4. 같은 물건을 다시 보여주면 quantity가 증가하는지 확인

### 4. DB 확인
```bash
# 장바구니 내역 확인
mysql -h database-1.chu0kq8imwi9.ap-northeast-2.rds.amazonaws.com -u root -p'Q!w2e3r4t5' smart_cart_db \
  -e "SELECT ci.*, p.name, p.price FROM cart_items ci 
      JOIN products p ON ci.product_id = p.product_id 
      WHERE ci.session_id=11;"
```

## 트러블슈팅

### UI에 상품이 안 나타날 때:
1. Main Hub 로그 확인: `tail -f main_hub.log`
   - "Product added:" 메시지가 있는지 확인
   
2. UI 터미널 확인:
   - "[UI] TCP server listening for commands on port 7001" 확인
   - UPDATE_CART 메시지 수신 로그 확인

3. DB 직접 확인:
   - cart_items에 데이터가 추가되는지 확인

### 웹캠에서 인식이 안 될 때:
1. Cart Camera 창에서 "프레임 0" 카운터가 증가하는지 확인
2. 물체가 충분히 크게 보이는지 확인 (최소 30% 화면)
3. YOLO confidence threshold (0.5) 이상인지 확인

## 성공 시 화면

### Cart Camera 창:
```
프레임: 35
웹캠 영상에 녹색 바운딩 박스
"ID:2 0.89" 라벨
```

### UI 장바구니:
```
Product         | Price  | Qty
----------------|--------|----
Monster Energy  | ₩ 3000 | 2
Mountain Dew    | ₩ 2500 | 1

Total Price: ₩ 8500
```

### Main Hub 로그:
```
INFO: [PRODUCT] Product 2 added (confidence=0.89)
INFO: [DB] Cart updated: 2 items, total=8500
```
