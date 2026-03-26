#!/bin/bash
# 毎日自動実行スクリプト
# cron例: 0 7 * * * /home/user/boat/run/daily.sh >> /home/user/boat/logs/daily.log 2>&1

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$REPO_DIR/logs"
mkdir -p "$LOG_DIR"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') 開始 ====="

# 今日の日付（JST）
TODAY=$(TZ='Asia/Tokyo' date '+%Y-%m-%d')
YESTERDAY=$(TZ='Asia/Tokyo' date -d 'yesterday' '+%Y-%m-%d')

cd "$REPO_DIR"

# 1. データダウンロード（前日分のKファイルと当日分のBファイル）
echo "[1/3] データダウンロード..."
python3 boat/download.py -dl -u -s "$YESTERDAY" -e "$TODAY" -bk BK
python3 boat/convert.py -k -b -i

# 2. 予想実行
echo "[2/3] 予想実行..."
cd run
python3 predictor.py
cd ..

echo "===== $(date '+%Y-%m-%d %H:%M:%S') 完了 ====="
