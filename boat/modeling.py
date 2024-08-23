import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import json

from config import *

set_values(globals())


import lightgbm as lgb
from sklearn.model_selection import train_test_split
def rank_model(df):
    raceids = df['RaceID'].unique()
    cross_val = 1
    cross_races = np.array_split(raceids, cross_val)
    
    races_t, races_v = train_test_split(raceids, test_size=0.2, random_state=42, shuffle=False)
    
    df_train = df.query('RaceID in @races_t').reset_index(drop=True)
    df_valid = df.query('RaceID in @races_v').reset_index(drop=True)
    rank = {1:6, 2:5, 3:4, 4:3, 5:2, 6:1}
    #dfのメモリを解放
    del df, raceids
    
    print(f'Train: {df_train.shape}')
    
    X_train = df_train.drop(columns=['着'])
    y_train = df_train['着'].apply(lambda x: rank[x])
    train_group = df_train.groupby('RaceID').size().tolist()
    
    X_valid = df_valid.drop(columns=['着'])
    y_valid = df_valid['着'].apply(lambda x: rank[x])
    valid_group = df_valid.groupby('RaceID').size().tolist()
    
    params = {
        'objective': 'lambdarank',
        'metric': 'ndcg',
        'ndcg_eval_at': [1,2,3],
        'boosting_type': 'gbdt',
        'seed' : 42,
        'num_leaves': 31,
        'max_depth': -1,
        'learning_rate': 0.05,
    }
    
    lgtrain = lgb.Dataset(X_train, y_train, group=train_group)
    lgvalid = lgb.Dataset(X_valid, y_valid, group=valid_group)
    
    callbacks = [
        lgb.early_stopping(stopping_rounds=300, verbose=True),
        lgb.log_evaluation(100),
    ]
    
    lgb_results = {}
    print('Training model...')
    model = lgb.train(
        params,
        lgtrain,
        num_boost_round=1500,
        valid_sets=[lgtrain, lgvalid],
        valid_names=['train','valid'],
        #evals_result=lgb_results,
        callbacks = callbacks
    )
    
    return model

def rank_predict(df, model):
    rank = {1:6, 2:5, 3:4, 4:3, 5:2, 6:1}
    X = df.drop(columns=['着'])
    y = df['着'].apply(lambda x: rank[x])
    group = df.groupby('RaceID').size().tolist()
    pred = model.predict(X)
    return pred