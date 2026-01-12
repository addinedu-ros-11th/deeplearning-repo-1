#!/bin/bash
# Git commit helper for obstacle_v2 integration

echo "=================================================="
echo "Git Commit Helper - obstacle_v2 Integration"
echo "=================================================="
echo ""

# Check git status
echo "📊 현재 Git 상태:"
git status --short | head -20
echo ""

# Show modified files count
modified=$(git status --short | wc -l)
echo "총 ${modified}개 파일 변경됨"
echo ""

# Suggested commit message
cat << 'EOF'
================================================
💡 권장 커밋 메시지:
================================================

feat: Integrate obstacle_v2 advanced tracking and risk assessment algorithm

🎯 주요 변경사항:
- 새로운 모듈 추가
  - src/detectors/obstacle_tracker.py (YOLO ByteTrack)
  - src/detectors/risk_engine.py (위험도 평가 엔진)
  
- 기존 모듈 업그레이드
  - src/detectors/obstacle_dl.py (완전 재구성)
  - src/core/engine.py (상세 위험도 처리)
  - src/common/config.py (risk 설정 추가)
  - src/database/obstacle_log_dao.py (새 필드 지원)

- DB 스키마 확장
  - obstacle_logs 테이블에 track_id, pttc_s, risk_score, in_center, approaching 필드 추가
  - scripts/update_obstacle_logs_schema.sql 생성

- 설정 업데이트
  - configs/model_config.yaml에 risk engine 파라미터 추가

- 테스트 및 문서
  - test/test_obstacle_integration.py (통합 테스트)
  - test/test_ai_server_ready.py (준비 상태 확인)
  - test/test_complete_integration.py (전체 테스트)
  - docs/OBSTACLE_INTEGRATION.md (상세 가이드)
  - INTEGRATION_COMPLETE_REPORT.md (완료 보고서)

✅ 기능 개선:
- 객체 추적: ByteTrack 알고리즘으로 Track ID 유지
- 위험도 평가: pTTC, 접근속도, 중앙위치 기반 정밀 판정
- 오감지 방지: Streak counting + Hysteresis
- 하위 호환: 기존 시스템과 완전 호환

🧪 테스트:
- 모든 통합 테스트 통과 (2/2)
- DB 스키마 업데이트 완료
- AI Server 준비 상태 확인 완료

================================================

EOF

echo ""
echo "📝 커밋 명령어 예시:"
echo "git add ."
echo 'git commit -F- << "COMMIT_MSG"'
echo "feat: Integrate obstacle_v2 advanced tracking and risk assessment"
echo ""
echo "- Add YOLO ByteTrack for object tracking"
echo "- Add risk engine with pTTC calculation"
echo "- Extend DB schema with tracking metrics"
echo "- Update configs and documentation"
echo "- All tests passing (2/2)"
echo "COMMIT_MSG"
echo ""
