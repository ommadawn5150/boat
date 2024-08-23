import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import json

import lightgbm as lgb
import json
from urllib.request import Request, urlopen
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

from config import *
set_values(globals())

model = lgb.Booster(model_file=f'../models/model_{frm}.txt')
from datetime import datetime as dt
from datetime import timedelta as td

diff = -5

today = (dt.now() + td(days=diff)).strftime('%Y%m%d')[2:]
df_today = pd.read_csv(f'../data/csv/B_files/B{today}.csv', index_col=0)

from data_loader import *
year = int(today[:2])
half = 'f' if int(today[2:]) < 700 else 'l'
rdf = get_racer_results(year, half).drop('体重',axis=1)
use_cols.remove('着')
df = pd.merge(df_today, rdf, on=['選手登番'], how='inner')[use_cols]

pred = model.predict(df, num_iteration=model.best_iteration)
df['pred'] = pred


races = df['RaceID'].unique()
place_code = {'桐生':'01','戸田':'02','江戸川':'03','平和島':'04','多摩川':'05','浜名湖':'06','蒲郡':'07','常滑':'08','津':'09','三国':'10','びわこ':'11','住之江':'12','尼崎':'13','鳴門':'14','丸亀':'15','児島':'16','宮島':'17','徳山':'18','下関':'19','若松':'20','芦屋':'21','福岡':'22','唐津':'23','大村':'24'}
_place_code = {v:k for k,v in place_code.items()}

n = 0
post_discord(f'## {today} 予想\n', WEBHOOK_DEBUG)
for raceid in races:
    race = df.query(f'RaceID == {raceid}')
    
    p = (race['pred'].argsort()[::-1] + 1).values
    _place = _place_code[f"{race['場所'].values[0]:02}"]
    r = race['R'].values[0]
    
    place = race['場所'].values[0]
    #nige = race['逃げ率'].values[0] > 0.4
    nige_s = race.query(f'艇番 == {p[0]}')['逃げ率'].values[0]
    nige = race.query(f'艇番 == {p[0]}')['逃げ率'].values[0] > 0.6
    female = sum(race['性別'].values) == 12
    ana = p[0] != 1
    pl = place in [21,24,19]
    pl = place in [3,2,4]
    
    if nige and pl and ana :
        buy = True
        n += 1
    else:
        buy = False
    
    pred_rank = ''
    for i in p:
        pred_rank += str(i)
    
    kaime = []
    kaime.append(pred_rank[:3])
    kaime.append(pred_rank[:2] + pred_rank[3])
    kaime.append(pred_rank[0] + pred_rank[2] + pred_rank[1])
    kaime.append(pred_rank[1] + pred_rank[0] + pred_rank[2])
    '''
    kaime.append(pred_rank[:2] + pred_rank[4])
    kaime.append(pred_rank[:2] + pred_rank[5])
    '''
    if buy:
        post = f'### {_place} {r}R : {pred_rank}\n'
        post += f'**買い目** :'
        for k in kaime:
            post += f'{k}, '
    
        print(post)
        post_discord(post, WEBHOOK_DEBUG)
    