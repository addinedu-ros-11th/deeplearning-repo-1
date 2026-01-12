-- 장애물 감지 로그 테이블에 고급 추적 정보 필드 추가
-- obstacle_v2 알고리즘 통합을 위한 스키마 업데이트

USE smart_cart_db;

-- track_id 컬럼 추가 (YOLO tracking ID)
ALTER TABLE obstacle_logs 
ADD COLUMN track_id INT DEFAULT -1 COMMENT 'YOLO Tracking ID (객체 추적용)';

-- pttc_s 컬럼 추가 (Predicted Time To Collision)
ALTER TABLE obstacle_logs 
ADD COLUMN pttc_s FLOAT DEFAULT NULL COMMENT 'Predicted Time To Collision (초, 충돌 예상 시간)';

-- risk_score 컬럼 추가 (위험도 점수)
ALTER TABLE obstacle_logs 
ADD COLUMN risk_score FLOAT DEFAULT NULL COMMENT 'Risk Score (위험도 점수)';

-- in_center 컬럼 추가 (중앙 영역 위치)
ALTER TABLE obstacle_logs 
ADD COLUMN in_center BOOLEAN DEFAULT FALSE COMMENT '중앙 영역 위치 여부';

-- approaching 컬럼 추가 (접근 중 여부)
ALTER TABLE obstacle_logs 
ADD COLUMN approaching BOOLEAN DEFAULT FALSE COMMENT '접근 중 여부';

-- 인덱스 추가 (track_id 기반 조회 성능 향상)
CREATE INDEX idx_obstacle_track_id ON obstacle_logs (track_id);

-- 인덱스 추가 (위험도 기반 조회)
CREATE INDEX idx_obstacle_risk ON obstacle_logs (is_warning, risk_score);

-- 완료 메시지
SELECT 'obstacle_logs 테이블 스키마 업데이트 완료 (obstacle_v2 통합)' AS status;
