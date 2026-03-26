# CLAUDE.md — AIアシスタント向けガイド (`boat`)

## プロジェクト概要

**boat** は競艇予想システムです。過去のレースデータをダウンロードし、レガシーな固定長テキスト形式を解析して特徴量を生成し、LightGBM LambdaRankモデルを学習させ、Discordのウェブフックを通じて毎日の予想を投稿します。

---

## リポジトリ構成

```
boat/
├── boat/                   # メインPythonパッケージ
│   ├── __init__.py
│   ├── config.py           # 設定ローダー：config.jsonからグローバル変数を設定
│   ├── config.json         # 全設定：パス、Discordウェブフック、特徴量カラム
│   ├── download.py         # mbrace.or.jpからLZHファイルをダウンロード・展開しUTF-8に変換
│   ├── convert.py          # 固定長テキストファイルをCSVに変換（BファイルとKファイル形式）
│   ├── data_loader.py      # B/K CSVをマージし43特徴量を生成、学習用DataFrameを構築
│   ├── modeling.py         # LightGBM LambdaRankモデルを学習・pickle保存
│   ├── prediction.py       # 予測ユーティリティ（スタブ／未実装）
│   └── racer.py            # レーサーLZHファイルを解析してレーサー統計CSVに変換
└── run/                    # 実行エントリーポイント
    ├── dl.sh               # 指定期間のレースデータをダウンロード・変換するシェルスクリプト
    ├── make_dataset.py     # 全CSVからpickleデータセットを構築
    ├── model.py            # LightGBMモデルの学習と評価
    ├── predictor.py        # ライブ予想を実行してDiscordに投稿
    └── calc.ipynb          # 探索的分析用Jupyterノートブック
```

---

## データパイプライン

```
mbrace.or.jp（LZHアーカイブ）
    ↓  download.py  — ダウンロード＋展開
UTF-8テキストファイル（固定長、Shift-JIS → UTF-8変換）
    ↓  convert.py   — バイトオフセットでカラムを切り出し
CSVファイル（K = レース結果、B = 番組・出場選手情報）
    ↓  data_loader.py — マージ＋特徴量エンジニアリング
Pandas DataFrame（レース出場艇ごとに43特徴量）
    ↓  make_dataset.py — 年ごとにpickle保存
pickleファイル（df15 〜 df24）
    ↓  model.py   — 学習・検証分割（2024-08-01基準）
LightGBMモデル（LambdaRank、NDCGメトリック）
    ↓  predictor.py — 毎日の予想
Discordウェブフック＋CSV結果ファイル
```

---

## 開発ワークフロー

### 1. レースデータのダウンロード
```bash
# dl.sh内の日付範囲を編集してから実行：
bash run/dl.sh
# 内部的には以下と同等：
python3 ./boat/download.py -dl -u -s YYYY-MM-DD -e YYYY-MM-DD -bk BK
python3 ./boat/convert.py -k -b -i
```

### 2. データセットの構築
```bash
# make_dataset.py内のfrmパラメータ（開始年、例：15 = 2015）を編集してから実行：
python3 run/make_dataset.py
```

### 3. モデルの学習
```bash
python3 run/model.py
```

### 4. 予想の実行
```bash
python3 run/predictor.py
```

---

## 設定ファイル（`boat/config.json`）

全ての実行時設定は `config.json` に集約されています。`.gitignore` の例外指定によりgitで追跡されます。

| キー | 説明 |
|------|------|
| `DIR_*` | LZH・TXT・CSV・レーサー・モデルデータのディレクトリパス |
| `WEBHOOK` | 予想出力用Discordウェブフック |
| `WEBHOOK_DEBUG` | デバッグ・エラー通知用Discordウェブフック |
| `URL_K`, `URL_B` | mbrace.or.jpのデータURL（K = 結果、B = 番組） |
| `INTERVAL` | ダウンロード間隔（秒）（デフォルト：1） |
| `TRAIN_FROM` | 学習データの開始年（例：`15` → 2015年） |
| `FEATURE_COLUMNS` | モデルで使用する43特徴量のリスト |
| `PLACE_CODE` | 競艇場名から数値コード（01〜24）へのマッピング |

モジュール内での設定読み込み：
```python
from boat.config import *   # set_values(globals()) によって全キーをグローバル変数として設定
```

---

## コード規約

### エンコーディング
- 元データはShift-JISエンコード。`download.py` と `convert.py` がUTF-8に変換します。
- プロジェクトが出力するCSVはすべてUTF-8です。

### ファイル命名規則
- 生アーカイブ：`k{YYMMDD}.lzh`（結果）、`b{YYMMDD}.lzh`（番組）
- 展開テキスト：同名で `.txt` 拡張子
- 変換済みCSV：同名で `.csv` 拡張子

### 固定長ファイルの解析
- `convert.py` はハードコードされたバイトオフセットでカラムを切り出します。
- これらのファイルにpandasのCSVパーサーを使わないでください。形式はバイナリ固定長です。

### 特徴量エンジニアリング
- 特徴量は `config.json` の `FEATURE_COLUMNS` リストで定義されています。
- 特徴量を変更する場合は `data_loader.py` と `config.json` の両方を更新してください。

### モデル仕様
- タスク：ランキング（LambdaRank）、二値分類ではありません。
- メトリック：NDCG
- 目的変数カラム：`rank`（整数1〜6、小さいほど上位着順）
- ランキングのグループキー：`race_id`

### インポートスタイル
- 各モジュールは `from boat.module import *` と `set_values(globals())` による設定注入を使用しています。
- この構造は設定伝播のために意図的に設計されています。変更しないでください。

---

## .gitignore に関する注意

以下はバージョン管理から意図的に除外されています：
- `*.csv`、`*.TXT`、`*.lzh`、`*.pkl`、`*.txt` — 全ての生データ・生成データ
- 例外：`!/boat/config.json` は明示的に追跡対象

データファイルをコミットしないでください。`config.json` の例外設定を削除しないでください。

---

## 依存ライブラリ

`requirements.txt` は存在しません。必要なライブラリ（pipで手動インストール）：

```
pandas
numpy
lightgbm
scikit-learn
matplotlib
polars
lhafile
requests
tqdm
geopy
```

---

## 既知の課題・未実装箇所

- **`prediction.py`** はスタブモジュールで未実装です。
- **自動テストなし** — 検証はコンソール出力と `calc.ipynb` で手動実施。
- **CI/CDなし** — `.github/workflows/` 等は存在しません。
- **ロギングフレームワークなし** — モジュールは `print()` を使用しています。
- **型ヒント・docstringなし** — ほとんどの関数に未記載。
- **config.jsonに認証情報** — DiscordウェブフックURLが平文で保存されています。
- **マジックナンバー** — `convert.py` のバイトオフセットはドキュメント化されていない定数です。

---

## Discord連携

`config.json` に定義されたDiscordウェブフック経由で予想結果を投稿します。`predictor.py` が予想CSVとレースサマリーをメッセージとして送信します。デバッグ・エラー通知は `WEBHOOK_DEBUG` に送られます。

---

## データソース

レースデータは日本モーターボート競走会のデータサービスから取得します：
- 結果（Kファイル）：`http://www1.mbrace.or.jp/od2/K/`
- 番組（Bファイル）：`http://www1.mbrace.or.jp/od2/B/`

ファイルはLZHアーカイブで、`{k|b}YYMMDD.lzh` の命名規則です。ダウンロードはconfigの `INTERVAL` 設定（デフォルト1秒）でリクエスト間隔を制御します。
