# CLAUDE.md — AI Assistant Guide for `boat`

## Project Overview

**boat** is a Japanese boat racing (競艇) prediction system. It downloads historical race data, parses legacy fixed-width text formats, engineers features, trains a LightGBM LambdaRank model, and posts daily race predictions to Discord via webhooks.

---

## Repository Structure

```
boat/
├── boat/                   # Main Python package
│   ├── __init__.py
│   ├── config.py           # Config loader; sets global variables from config.json
│   ├── config.json         # All configuration: paths, Discord webhooks, feature columns
│   ├── download.py         # Downloads LZH race files from mbrace.or.jp; decompresses to UTF-8
│   ├── convert.py          # Parses fixed-width text files → CSV (B and K file formats)
│   ├── data_loader.py      # Merges B/K CSVs, engineers 43 features, builds training DataFrame
│   ├── modeling.py         # Trains LightGBM LambdaRank model; saves to pickle
│   ├── prediction.py       # Prediction utilities (stub/incomplete)
│   └── racer.py            # Parses racer LZH files → racer stats CSV
└── run/                    # Executable entry points
    ├── dl.sh               # Downloads and converts race data for a date range
    ├── make_dataset.py     # Builds the pickle dataset from all CSVs
    ├── model.py            # Trains and evaluates the LightGBM model
    ├── predictor.py        # Runs live predictions and posts results to Discord
    └── calc.ipynb          # Exploratory Jupyter notebook
```

---

## Data Pipeline

```
mbrace.or.jp (LZH archives)
    ↓  download.py  — download + decompress
UTF-8 text files (fixed-width, legacy Shift-JIS → UTF-8)
    ↓  convert.py   — parse byte-offset columns
CSV files  (K = race results,  B = program/participant info)
    ↓  data_loader.py — merge + feature engineering
Pandas DataFrame  (43 features per boat/race entry)
    ↓  make_dataset.py — save as pickle per year half
Pickle files  (df15 … df24)
    ↓  model.py   — train/validate split at 2024-08-01
LightGBM model (LambdaRank, NDCG metric)
    ↓  predictor.py — daily predictions
Discord webhook + CSV results file
```

---

## Standard Development Workflow

### 1. Download Race Data
```bash
# Edit dl.sh date range, then run:
bash run/dl.sh
# Equivalent to:
python3 ./boat/download.py -dl -u -s YYYY-MM-DD -e YYYY-MM-DD -bk BK
python3 ./boat/convert.py -k -b -i
```

### 2. Build Dataset
```bash
# Edit the `frm` variable (start year, e.g. 15 = 2015) inside make_dataset.py first
python3 run/make_dataset.py
```

### 3. Train Model
```bash
python3 run/model.py
```

### 4. Run Predictions
```bash
python3 run/predictor.py
```

---

## Configuration (`boat/config.json`)

All runtime configuration lives in `config.json`. It is explicitly tracked by git (see `.gitignore` exception).

Key sections:

| Key | Description |
|-----|-------------|
| `DIR_*` | Paths to LZH, TXT, CSV, racer, and model data directories |
| `WEBHOOK` | Discord webhook for prediction output |
| `WEBHOOK_DEBUG` | Discord webhook for debug/error messages |
| `URL_K`, `URL_B` | Source URLs at mbrace.or.jp (K = results, B = program) |
| `INTERVAL` | Seconds to wait between download requests (default: 1) |
| `TRAIN_FROM` | Year integer to begin training data (e.g. `15` → 2015) |
| `FEATURE_COLUMNS` | List of 43 feature names used by the model |
| `PLACE_CODE` | Map of venue names to numeric codes (01–24) |

To load config in a module:
```python
from boat.config import *   # sets all keys as module-level globals via set_values(globals())
```

---

## Key Conventions

### Encoding
- Source data is Shift-JIS encoded; `download.py` and `convert.py` convert to UTF-8.
- All CSV files written by the project are UTF-8.

### File Naming
- Raw archives: `k{YYMMDD}.lzh` (results) and `b{YYMMDD}.lzh` (program).
- Extracted text: same name with `.txt` extension.
- Converted CSVs: same base name with `.csv`.

### Fixed-Width Parsing
- `convert.py` uses hard-coded byte offsets to slice columns from legacy text files.
- Do not add pandas-based CSV parsing for these files — the format is binary/fixed-width.

### Feature Engineering
- Features are defined by the `FEATURE_COLUMNS` list in `config.json`.
- Changes to features require updating both `data_loader.py` and `config.json`.

### Model
- Task: ranking (LambdaRank), not binary classification.
- Metric: NDCG.
- Target column: `rank` (integer 1–6, lower = better finish position).
- Group key for ranking: `race_id`.

### Import Style
- Modules use `from boat.module import *` with `set_values(globals())` for config injection.
- Avoid restructuring this pattern — it is intentional for config propagation.

---

## Gitignore Notes

The following are intentionally excluded from version control:
- `*.csv`, `*.TXT`, `*.lzh`, `*.pkl`, `*.txt` — all raw/generated data
- Exception: `!/boat/config.json` is explicitly tracked

Do **not** commit data files. Do **not** remove the `config.json` gitignore exception.

---

## Dependencies

No `requirements.txt` exists. Key libraries (install manually or via pip):

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

## Known Limitations / Incomplete Areas

- **`prediction.py`** is a stub module — not yet fully implemented.
- **No automated tests** — validation is done manually via console output and `calc.ipynb`.
- **No CI/CD** — no `.github/workflows/` or similar.
- **No logging framework** — modules use `print()`.
- **No type hints or docstrings** on most functions.
- **Credentials in config.json** — Discord webhook URLs are stored in plaintext.
- **Magic numbers** — byte offsets in `convert.py` are undocumented constants.

---

## Discord Integration

Predictions are posted via Discord webhooks defined in `config.json`. The `predictor.py` script sends prediction CSVs and race summaries as messages. Debug/error notifications go to `WEBHOOK_DEBUG`.

---

## Data Source

Race data is fetched from the Japan Motorboat Racing Association's data service:
- Results (K files): `http://www1.mbrace.or.jp/od2/K/`
- Program (B files): `http://www1.mbrace.or.jp/od2/B/`

Files are LZH archives named `{k|b}YYMMDD.lzh`. The download respects a 1-second interval between requests (`INTERVAL` in config).
