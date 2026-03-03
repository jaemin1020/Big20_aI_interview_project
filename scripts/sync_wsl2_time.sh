#!/bin/bash
# scripts/sync_wsl2_time.sh
# WSL2 시간 동기화 스크립트
# 윈도우 절전 모드 복귀 시 WSL2 시간이 호스트(Window)와 차이가 발생하여 
# Celery 워커의 하트비트(Heartbeat) 오류가 나는 현상을 해결합니다.

echo "🔄 [Time-Sync] WSL2 시간 동기화 중..."
# sudo 권한이 필요할 수 있습니다.
sudo hwclock -s
echo "✅ [Time-Sync] 동기화 완료: $(date)"
