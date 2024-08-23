import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import json
import sys
import glob 
sys.path.append('../boat/')
sys.path.append('../')
import pickle

with open('../boat/config.json', 'r') as f:
    config = json.load(f)
USE_COLS = config['pred']['use_cols']
FRM = config['pred']['frm']

modeling = True # モデルを学習するかどうか
actual = True # 本番の予測を行うかどうか

with open(f'../data/pickle/df{FRM}.pkl', 'rb') as f:
    df = pickle.load(f)[USE_COLS]
print(df.info())

from sklearn.model_selection import train_test_split

if actual == True:
    crt = 202408010000
    train_df = df.query(f'RaceID < {crt}').reset_index(drop=True)
    valid_df = df.query(f'RaceID >= {crt}').reset_index(drop=True)

else:
    train_df = df.query(f'RaceID < 202405010000').reset_index(drop=True)
    valid_df = df.query(f'RaceID >= 202405010000').reset_index(drop=True)


from modeling import *
if modeling == True:
    model = rank_model(train_df)
    model.save_model(f'../models/model_{FRM}.txt')
else:
    model = lgb.Booster(model_file=f'../models/model_{FRM}.txt')

print(model.best_score)

pred = model.predict(valid_df.drop(columns=['着']), num_iteration=model.best_iteration)

with open(f'../pred/pred_{FRM}.pkl', 'wb') as f:
    pickle.dump(pred, f)

valid_df['pred'] = pred
valid_df.to_csv(f'../pred/pred_{FRM}.csv', index=False)

print(valid_df.info())