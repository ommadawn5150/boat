#!/bin/bash
# サーバーセットアップスクリプト
# 新規VPSでの初回セットアップ時に実行してください
# 使い方: bash setup.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_USER="${SUDO_USER:-$(whoami)}"

echo "======================================"
echo " boat racing prediction server setup"
echo "======================================"

# --- 1. システムパッケージ ---
echo "[1/6] システムパッケージをインストール..."
sudo apt-get update -q
sudo apt-get install -y python3 python3-pip python3-venv git lhasa cron

# --- 2. Python仮想環境 ---
echo "[2/6] Python仮想環境を構築..."
python3 -m venv "$REPO_DIR/venv"
source "$REPO_DIR/venv/bin/activate"
pip install --upgrade pip -q
pip install -r "$REPO_DIR/requirements.txt" -q
echo "依存ライブラリのインストール完了"

# --- 3. データディレクトリ作成 ---
echo "[3/6] データディレクトリを作成..."
mkdir -p "$REPO_DIR/data/DL/results_lzh"
mkdir -p "$REPO_DIR/data/DL/bangumi_lzh"
mkdir -p "$REPO_DIR/data/DL/results_unlzh"
mkdir -p "$REPO_DIR/data/DL/bangumi_unlzh"
mkdir -p "$REPO_DIR/data/DL/racer_lzh"
mkdir -p "$REPO_DIR/data/txt/K_files"
mkdir -p "$REPO_DIR/data/txt/B_files"
mkdir -p "$REPO_DIR/data/txt/K_files_converted"
mkdir -p "$REPO_DIR/data/txt/B_files_converted"
mkdir -p "$REPO_DIR/data/txt/racer_txt"
mkdir -p "$REPO_DIR/data/csv/K_files"
mkdir -p "$REPO_DIR/data/csv/B_files"
mkdir -p "$REPO_DIR/data/csv/Race_info"
mkdir -p "$REPO_DIR/data/csv/racer_csv"
mkdir -p "$REPO_DIR/models"
mkdir -p "$REPO_DIR/pred"
mkdir -p "$REPO_DIR/logs"
chmod +x "$REPO_DIR/run/daily.sh"
chmod +x "$REPO_DIR/run/retrain.sh"
echo "ディレクトリ作成完了"

# --- 4. Discordボットのsystemdサービス設定 ---
echo "[4/6] systemdサービスを設定..."
SERVICE_FILE="$REPO_DIR/systemd/boat-bot.service"
INSTALL_SERVICE="/etc/systemd/system/boat-bot.service"

# サービスファイルのパスとユーザーを実環境に合わせて書き換え
sed "s|/home/boat/boat|$REPO_DIR|g; s|User=boat|User=$INSTALL_USER|g" \
    "$SERVICE_FILE" | sudo tee "$INSTALL_SERVICE" > /dev/null

echo ""
echo "  !! Discordボットトークンを設定してください !!"
echo "  sudo nano $INSTALL_SERVICE"
echo "  → Environment=\"DISCORD_BOT_TOKEN=実際のトークン\""
echo ""

sudo systemctl daemon-reload

# --- 5. cron設定 ---
echo "[5/6] cronジョブを設定..."
CRON_DAILY="0 7 * * * $REPO_DIR/venv/bin/python3 -c 'import subprocess; subprocess.run([\"bash\", \"$REPO_DIR/run/daily.sh\"])' >> $REPO_DIR/logs/daily.log 2>&1"
CRON_RETRAIN="0 3 1 * * bash $REPO_DIR/run/retrain.sh >> $REPO_DIR/logs/retrain.log 2>&1"

# 既存のcronに追記（重複チェック付き）
(crontab -l 2>/dev/null | grep -v 'boat'; \
 echo "$CRON_DAILY"; \
 echo "$CRON_RETRAIN") | crontab -

echo "cronジョブ設定完了:"
crontab -l | grep boat

# --- 6. セットアップ完了メッセージ ---
echo ""
echo "======================================"
echo " セットアップ完了！"
echo "======================================"
echo ""
echo "次のステップ:"
echo ""
echo "  1. Discordボットトークンを設定"
echo "     sudo nano $INSTALL_SERVICE"
echo "     → YOUR_TOKEN_HERE を実際のトークンに置き換え"
echo ""
echo "  2. 過去データをダウンロード（初回のみ）"
echo "     source $REPO_DIR/venv/bin/activate"
echo "     bash $REPO_DIR/run/dl.sh"
echo ""
echo "  3. データセット構築 & モデル学習（初回のみ）"
echo "     cd $REPO_DIR/run && python3 make_dataset.py && python3 model.py"
echo ""
echo "  4. Discordボットを起動"
echo "     sudo systemctl enable --now boat-bot"
echo "     sudo systemctl status boat-bot"
echo ""
echo "  5. ログ確認"
echo "     journalctl -u boat-bot -f       # ボットのログ"
echo "     tail -f $REPO_DIR/logs/daily.log  # 日次処理のログ"
echo ""
