#!/bin/bash
# 月次モデル再学習スクリプト
# cron例: 0 3 1 * * /home/user/boat/run/retrain.sh >> /home/user/boat/logs/retrain.log 2>&1

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$REPO_DIR/logs"
mkdir -p "$LOG_DIR"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') 再学習開始 ====="

cd "$REPO_DIR/run"

echo "[1/2] データセット再構築..."
python3 make_dataset.py

echo "[2/2] モデル学習..."
python3 model.py

echo "===== $(date '+%Y-%m-%d %H:%M:%S') 再学習完了 ====="
