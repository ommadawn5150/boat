import numpy as np
import pandas as pd
import os
import json
from urllib.request import Request, urlopen
from datetime import datetime as dt
from datetime import timedelta as td

def post_discord(message: str, webhook_url: str):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (private use) Python-urllib/3.10",
    }
    data = {"content": message}
    request = Request(
        webhook_url,
        data=json.dumps(data).encode(),
        headers=headers,
    )
    with urlopen(request) as res:
        assert res.getcode() == 204

import sys
sys.path.append('../')
sys.path.append('../boat/')

import lightgbm as lgb
from config import *
set_values(globals())

from data_loader import *

model = lgb.Booster(model_file=f'../models/model_{frm}.txt')

diff = -5
today = (dt.now() + td(days=diff)).strftime('%Y%m%d')[2:]
df_today = pd.read_csv(f'../data/csv/B_files/B{today}.csv', index_col=0)

year = int(today[:2])
half = 'f' if int(today[2:]) < 700 else 'l'
rdf = get_racer_results(year, half).drop('体重', axis=1)

# use_cols からグローバルリストを破壊せずに '着' を除いたリストを作成
predict_cols = [c for c in use_cols if c != '着']

df = pd.merge(df_today, rdf, on=['選手登番'], how='inner')[predict_cols]

pred = model.predict(df, num_iteration=model.best_iteration)
df['pred'] = pred

races = df['RaceID'].unique()
_place_code = {int(v): k for k, v in PLACE_CODE.items()}

# ROI追跡用に予想履歴を保存
history_path = '../pred/history.csv'
history_rows = []

n = 0
post_discord(f'## {today} 予想\n', WEBHOOK_DEBUG)
for raceid in races:
    race = df.query(f'RaceID == {raceid}')

    p = (race['pred'].argsort()[::-1] + 1).values
    place = race['場所'].values[0]
    _place = _place_code.get(place, str(place))
    r = race['R'].values[0]

    nige = race.query(f'艇番 == {p[0]}')['逃げ率'].values[0] > 0.6
    ana = p[0] != 1
    pl = place in ACTIVE_PLACES

    pred_rank = ''.join(str(i) for i in p)

    kaime = [
        pred_rank[:3],
        pred_rank[:2] + pred_rank[3],
        pred_rank[0] + pred_rank[2] + pred_rank[1],
        pred_rank[1] + pred_rank[0] + pred_rank[2],
    ]

    buy = nige and pl and ana
    if buy:
        n += 1
        post = f'### {_place} {r}R : {pred_rank}\n'
        post += f'**買い目** :'
        for k in kaime:
            post += f'{k}, '
        print(post)
        post_discord(post, WEBHOOK_DEBUG)

    # 予想履歴を記録（買い目の有無を問わず全レース保存）
    history_rows.append({
        'date': today,
        'RaceID': raceid,
        'place': _place,
        'R': r,
        'pred_rank': pred_rank,
        'kaime': '|'.join(kaime),
        'buy': buy,
    })

# history.csv に追記
history_df = pd.DataFrame(history_rows)
if os.path.exists(history_path):
    history_df.to_csv(history_path, mode='a', header=False, index=False)
else:
    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    history_df.to_csv(history_path, index=False)

print(f'本日の買い目レース数: {n}')
