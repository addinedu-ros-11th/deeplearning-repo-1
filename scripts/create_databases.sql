CREATE TABLE `categories` (
  `category_id` int PRIMARY KEY AUTO_INCREMENT COMMENT '카테고리 고유 ID',
  `name` varchar(50) NOT NULL COMMENT '카테고리 명칭'
);

CREATE TABLE `products` (
  `product_id` int PRIMARY KEY AUTO_INCREMENT COMMENT '상품 고유 ID',
  `category_id` int NOT NULL COMMENT '카테고리 ID',
  `name` varchar(100) NOT NULL COMMENT '상품명',
  `price` int NOT NULL COMMENT '개별 가격 (원화)',
  `stock_quantity` int NOT NULL COMMENT '현재 재고 수량',
  `updated_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP) COMMENT '정보 수정 일시'
);

CREATE TABLE `carts` (
  `cart_id` int PRIMARY KEY AUTO_INCREMENT COMMENT '시스템 관리 ID',
  `cart_code` varchar(50) UNIQUE NOT NULL COMMENT '기기 시리얼 넘버/식별코드',
  `status` ENUM ('AVAILABLE', 'IN_USE', 'MAINTENANCE') NOT NULL DEFAULT 'AVAILABLE' COMMENT '카트 상태'
);

CREATE TABLE `shopping_sessions` (
  `session_id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '세션 고유 ID',
  `cart_id` int NOT NULL COMMENT '사용된 카트 ID',
  `start_time` datetime NOT NULL COMMENT '사용 시작 시간',
  `end_time` datetime COMMENT '사용 종료 시간',
  `status` ENUM ('ACTIVE', 'COMPLETED') NOT NULL DEFAULT 'ACTIVE' COMMENT '세션 상태'
);

CREATE TABLE `cart_items` (
  `item_id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '항목 고유 ID',
  `session_id` bigint NOT NULL COMMENT '쇼핑 세션 ID',
  `product_id` int NOT NULL COMMENT '인식된 상품 ID',
  `quantity` int NOT NULL DEFAULT 1 COMMENT '수량',
  `added_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP) COMMENT '인식 시간'
);

CREATE TABLE `quality_logs` (
  `log_id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '로그 ID',
  `session_id` bigint NOT NULL COMMENT '쇼핑 세션 ID',
  `product_id` int COMMENT '추정 상품 ID (미인식 시 NULL)',
  `defect_type` varchar(50) COMMENT '결함 유형 (구겨짐, 파손 등)',
  `snapshot_url` varchar(255) COMMENT '결함 당시 캡처 이미지 URL',
  `detected_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP) COMMENT '감지 시간'
);

CREATE TABLE `obstacle_logs` (
  `log_id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '로그 ID',
  `session_id` bigint NOT NULL COMMENT '쇼핑 세션 ID',
  `object_type` varchar(20) NOT NULL COMMENT '장애물 종류 (PERSON, CART)',
  `distance` float COMMENT '거리 (단위: m)',
  `speed` float COMMENT '상대 속도 (단위: m/s)',
  `direction` varchar(20) COMMENT '방향 (FRONT, LEFT 등)',
  `is_warning` boolean NOT NULL DEFAULT false COMMENT '충돌 경고 발생 여부',
  `detected_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP) COMMENT '감지 시간',
  `track_id` int DEFAULT -1 COMMENT 'YOLO Tracking ID (객체 추적용)',
  `pttc_s` float DEFAULT NULL COMMENT 'Predicted Time To Collision (초)',
  `risk_score` float DEFAULT NULL COMMENT 'Risk Score (위험도 점수)',
  `in_center` boolean DEFAULT false COMMENT '중앙 영역 위치 여부',
  `approaching` boolean DEFAULT false COMMENT '접근 중 여부'
);

CREATE TABLE `orders` (
  `order_id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '주문 번호',
  `session_id` bigint UNIQUE NOT NULL COMMENT '쇼핑 세션 ID',
  `total_amount` int NOT NULL COMMENT '총 결제 금액',
  `total_items` int NOT NULL COMMENT '총 품목 개수',
  `purchased_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP) COMMENT '결제 완료 시간'
);

CREATE TABLE `order_details` (
  `detail_id` bigint PRIMARY KEY AUTO_INCREMENT COMMENT '상세 ID',
  `order_id` bigint NOT NULL COMMENT '주문 번호',
  `product_id` int NOT NULL COMMENT '상품 ID',
  `snap_price` int NOT NULL COMMENT '구매 당시 가격',
);

CREATE INDEX `products_index_0` ON `products` (`category_id`);

CREATE INDEX `products_index_1` ON `products` (`updated_at`);

CREATE INDEX `shopping_sessions_index_2` ON `shopping_sessions` (`cart_id`, `status`);

CREATE INDEX `shopping_sessions_index_3` ON `shopping_sessions` (`start_time`);

CREATE INDEX `cart_items_index_4` ON `cart_items` (`session_id`);

CREATE INDEX `cart_items_index_5` ON `cart_items` (`added_at`);

CREATE INDEX `quality_logs_index_6` ON `quality_logs` (`session_id`, `detected_at`);

CREATE INDEX `quality_logs_index_7` ON `quality_logs` (`defect_type`);

CREATE INDEX `obstacle_logs_index_8` ON `obstacle_logs` (`session_id`, `is_warning`);

CREATE INDEX `obstacle_logs_index_9` ON `obstacle_logs` (`detected_at`);

CREATE INDEX `obstacle_logs_index_10` ON `obstacle_logs` (`track_id`);

CREATE INDEX `obstacle_logs_index_11` ON `obstacle_logs` (`is_warning`, `risk_score`);

CREATE INDEX `orders_index_12` ON `orders` (`purchased_at`);

CREATE INDEX `order_details_index_13` ON `order_details` (`order_id`);

ALTER TABLE `categories` COMMENT = 'TB-01: 상품 카테고리 마스터 (아이스크림, 과자, 라면 등)';

ALTER TABLE `products` COMMENT = 'TB-02: 상품 정보 마스터';

ALTER TABLE `carts` COMMENT = 'TB-03: 카트 디바이스 정보';

ALTER TABLE `shopping_sessions` COMMENT = 'TB-04: 쇼핑 세션 (카트 사용 시작부터 종료까지)';

ALTER TABLE `cart_items` COMMENT = 'TB-05: 장바구니 담기 내역';

ALTER TABLE `quality_logs` COMMENT = 'TB-06: 품질 검사 로그 (기하학적 변형/파손 감지)';

ALTER TABLE `obstacle_logs` COMMENT = 'TB-07: 장애물 인식 로그 (주행 안전 모니터링)';

ALTER TABLE `orders` COMMENT = 'TB-08: 구매 확정 정보';

ALTER TABLE `order_details` COMMENT = 'TB-09: 구매 상세 스냅샷 (가격 변동 대비 보존)';

ALTER TABLE `products` ADD FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`);

ALTER TABLE `shopping_sessions` ADD FOREIGN KEY (`cart_id`) REFERENCES `carts` (`cart_id`);

ALTER TABLE `cart_items` ADD FOREIGN KEY (`session_id`) REFERENCES `shopping_sessions` (`session_id`);

ALTER TABLE `cart_items` ADD FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`);

ALTER TABLE `quality_logs` ADD FOREIGN KEY (`session_id`) REFERENCES `shopping_sessions` (`session_id`);

ALTER TABLE `quality_logs` ADD FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`);

ALTER TABLE `obstacle_logs` ADD FOREIGN KEY (`session_id`) REFERENCES `shopping_sessions` (`session_id`);

ALTER TABLE `orders` ADD FOREIGN KEY (`session_id`) REFERENCES `shopping_sessions` (`session_id`);

ALTER TABLE `order_details` ADD FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`);

ALTER TABLE `order_details` ADD FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`);
