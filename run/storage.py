"""
S3互換ストレージ（AWS S3 / Cloudflare R2 / Backblaze B2）との
ファイル同期ユーティリティ。

必要な環境変数:
  S3_BUCKET        — バケット名
  S3_ACCESS_KEY    — アクセスキー
  S3_SECRET_KEY    — シークレットキー
  S3_ENDPOINT_URL  — エンドポイント（R2の場合は必須、S3はオプション）

使い方:
  python3 run/storage.py download   # モデル・レーサーCSVをS3から取得
  python3 run/storage.py upload     # モデル・レーサーCSVをS3にアップロード
"""

import os
import sys
import boto3
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / 'boat'))
from config import *
set_values(globals())

REPO_DIR = Path(__file__).parent.parent

def get_client():
    kwargs = {
        'aws_access_key_id': os.environ['S3_ACCESS_KEY'],
        'aws_secret_access_key': os.environ['S3_SECRET_KEY'],
        'region_name': os.environ.get('S3_REGION', 'auto'),
    }
    endpoint = os.environ.get('S3_ENDPOINT_URL')
    if endpoint:
        kwargs['endpoint_url'] = endpoint
    return boto3.client('s3', **kwargs)

BUCKET = os.environ.get('S3_BUCKET', '')

# S3に保存するファイルの定義
SYNC_FILES = [
    # (ローカルパス, S3キー)
    (REPO_DIR / f'models/model_{frm}.txt', f'models/model_{frm}.txt'),
    (REPO_DIR / 'pred/history.csv', 'pred/history.csv'),
]

def racer_csv_files():
    """レーサーCSVファイル一覧を返す"""
    racer_dir = Path(RACER_CSV)
    return [(f, f'racer_csv/{f.name}') for f in racer_dir.glob('fan*.csv')]

def download():
    client = get_client()
    targets = SYNC_FILES + racer_csv_files()
    for local_path, s3_key in targets:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            print(f'  ↓ {s3_key}')
            client.download_file(BUCKET, s3_key, str(local_path))
        except client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f'    (スキップ: S3に存在しません)')
            else:
                raise

def upload():
    client = get_client()
    targets = SYNC_FILES + racer_csv_files()
    for local_path, s3_key in targets:
        if not local_path.exists():
            print(f'  (スキップ: {local_path} が存在しません)')
            continue
        print(f'  ↑ {s3_key}')
        client.upload_file(str(local_path), BUCKET, s3_key)

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'download'
    if cmd == 'download':
        print('S3からダウンロード中...')
        download()
        print('完了')
    elif cmd == 'upload':
        print('S3へアップロード中...')
        upload()
        print('完了')
    else:
        print(f'不明なコマンド: {cmd}')
        sys.exit(1)
