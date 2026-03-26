"""
ストレージバックエンド切替対応のファイル同期ユーティリティ。
環境変数 STORAGE_BACKEND で切り替え（デフォルト: gdrive）。

--- Google Drive ---
必要な環境変数:
  GDRIVE_FOLDER_ID        — 保存先フォルダのID（URLの末尾部分）
  GDRIVE_SERVICE_ACCOUNT  — サービスアカウントのJSONキー（文字列）

--- S3互換（AWS S3 / Cloudflare R2 / Backblaze B2） ---
必要な環境変数:
  S3_BUCKET        — バケット名
  S3_ACCESS_KEY    — アクセスキー
  S3_SECRET_KEY    — シークレットキー
  S3_ENDPOINT_URL  — エンドポイント（R2の場合は必須、S3はオプション）

使い方:
  python3 run/storage.py download   # モデル・レーサーCSVをダウンロード
  python3 run/storage.py upload     # モデル・レーサーCSVをアップロード
"""

import os
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / 'boat'))
from config import *
set_values(globals())

REPO_DIR = Path(__file__).parent.parent

# 同期対象ファイルの定義: (ローカルパス, ストレージ上のファイル名)
def sync_targets():
    targets = [
        (REPO_DIR / f'models/model_{frm}.txt', f'model_{frm}.txt'),
        (REPO_DIR / 'pred/history.csv', 'history.csv'),
    ]
    racer_dir = Path(RACER_CSV)
    if racer_dir.exists():
        for f in racer_dir.glob('fan*.csv'):
            targets.append((f, f'racer_{f.name}'))
    return targets


# ─── Google Drive バックエンド ────────────────────────────────────────────

def _gdrive_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    key_json = os.environ['GDRIVE_SERVICE_ACCOUNT']
    info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds, cache_discovery=False)

def _gdrive_file_map(service, folder_id):
    """フォルダ内のファイル名→IDの辞書を返す"""
    result = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields='files(id, name)',
        pageSize=200,
    ).execute()
    return {f['name']: f['id'] for f in result.get('files', [])}

def gdrive_download():
    from googleapiclient.http import MediaIoBaseDownload
    import io

    service = _gdrive_service()
    folder_id = os.environ['GDRIVE_FOLDER_ID']
    file_map = _gdrive_file_map(service, folder_id)

    for local_path, remote_name in sync_targets():
        if remote_name not in file_map:
            print(f'  (スキップ: {remote_name} がDriveに存在しません)')
            continue
        local_path.parent.mkdir(parents=True, exist_ok=True)
        print(f'  ↓ {remote_name}')
        fh = io.FileIO(str(local_path), 'wb')
        downloader = MediaIoBaseDownload(
            fh, service.files().get_media(fileId=file_map[remote_name])
        )
        done = False
        while not done:
            _, done = downloader.next_chunk()

def gdrive_upload():
    from googleapiclient.http import MediaFileUpload

    service = _gdrive_service()
    folder_id = os.environ['GDRIVE_FOLDER_ID']
    file_map = _gdrive_file_map(service, folder_id)

    for local_path, remote_name in sync_targets():
        if not local_path.exists():
            print(f'  (スキップ: {local_path} が存在しません)')
            continue
        print(f'  ↑ {remote_name}')
        media = MediaFileUpload(str(local_path), resumable=True)
        if remote_name in file_map:
            # 既存ファイルを上書き
            service.files().update(
                fileId=file_map[remote_name], media_body=media
            ).execute()
        else:
            # 新規作成
            service.files().create(
                body={'name': remote_name, 'parents': [folder_id]},
                media_body=media,
            ).execute()


# ─── S3互換バックエンド ──────────────────────────────────────────────────

def _s3_client():
    import boto3
    kwargs = {
        'aws_access_key_id': os.environ['S3_ACCESS_KEY'],
        'aws_secret_access_key': os.environ['S3_SECRET_KEY'],
        'region_name': os.environ.get('S3_REGION', 'auto'),
    }
    if endpoint := os.environ.get('S3_ENDPOINT_URL'):
        kwargs['endpoint_url'] = endpoint
    return boto3.client('s3', **kwargs)

def s3_download():
    import botocore
    client = _s3_client()
    bucket = os.environ['S3_BUCKET']
    for local_path, remote_name in sync_targets():
        local_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            print(f'  ↓ {remote_name}')
            client.download_file(bucket, remote_name, str(local_path))
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f'    (スキップ: S3に存在しません)')
            else:
                raise

def s3_upload():
    client = _s3_client()
    bucket = os.environ['S3_BUCKET']
    for local_path, remote_name in sync_targets():
        if not local_path.exists():
            print(f'  (スキップ: {local_path} が存在しません)')
            continue
        print(f'  ↑ {remote_name}')
        client.upload_file(str(local_path), bucket, remote_name)


# ─── エントリーポイント ──────────────────────────────────────────────────

BACKEND = os.environ.get('STORAGE_BACKEND', 'gdrive')

def download():
    if BACKEND == 'gdrive':
        gdrive_download()
    else:
        s3_download()

def upload():
    if BACKEND == 'gdrive':
        gdrive_upload()
    else:
        s3_upload()

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'download'
    label = 'Google Drive' if BACKEND == 'gdrive' else 'S3'
    if cmd == 'download':
        print(f'{label} からダウンロード中...')
        download()
        print('完了')
    elif cmd == 'upload':
        print(f'{label} へアップロード中...')
        upload()
        print('完了')
    else:
        print(f'不明なコマンド: {cmd}')
        sys.exit(1)
