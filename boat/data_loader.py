import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import json
pd.set_option('display.max_columns', None)

import sys
os.path.abspath(os.path.join('..'))
import glob

import polars as pl
import lightgbm as lgb
import re

import config
gl = globals()
config.set_values(gl)

def half_list(files, year, half):
    if half == 'f':
        hl = sorted([i for i in files if year * 10000 + 700 > int(i) > year * 10000 + 100 ])
    else :
        hl = sorted([i for i in files if year * 10000 + 10100 > int(i) > year * 10000 + 700 ]) 
    return hl

def read_csv(files, kind):

    if kind == 'B':
        path = CSV_DIR_B + f'{kind}{files[0]}.csv'
        df = pd.read_csv(path, index_col=0)
        for f in files[1:]:
            path = CSV_DIR_B + f'{kind}{f}.csv'
            df = pd.concat([df, pd.read_csv(path, index_col=0)])
    else :
        path = CSV_DIR_K + f'{kind}{files[0]}.csv'
        df = pd.read_csv(path, usecols=['RaceID','着','選手登番','単勝_結果','単勝_払戻','2連単_結果','2連単_払戻','2連単_人気','3連単_結果','3連単_払戻','3連単_人気'])
        for f in files[1:]:
            path = CSV_DIR_K + f'{kind}{f}.csv'
            df = pd.concat([df, pd.read_csv(path, usecols=['RaceID','着','選手登番','単勝_結果','単勝_払戻','2連単_結果','2連単_払戻','2連単_人気','3連単_結果','3連単_払戻','3連単_人気'])])
    return df

def get_racer_results(year, half):
    m = '10' if half == 'f' else '04'
    if half == 'f': year = year - 1
    df = pd.read_csv(f'{RACER_CSV}fan{year}{m}.csv')
    df['逃げ率'] = df['1コース1着回数'] / df['1コース進入回数']
    df['逃げ率'] = df['逃げ率'].fillna(0)
    df['差し率'] = df['2コース1着回数'] / df['2コース進入回数']
    df['差し率'] = df['差し率'].fillna(0)
    df['まくり率'] = (df['3コース1着回数'] + df['4コース1着回数'] + df['5コース1着回数'] + df['6コース1着回数'])/ (df['3コース進入回数'] + df['4コース進入回数'] + df['5コース進入回数'] + df['6コース進入回数'])
    df['まくり率'] = df['まくり率'].fillna(0)
    df['1コースまくられ率'] = (df['1コース進入回数'] - df['1コース1着回数'] -  df['1コース2着回数'])/df['1コース進入回数']
    df['1コースまくられ率'] = df['1コースまくられ率'].fillna(0)
    #df['1コース差され率'] = (df['1コース進入回数'] - df['1コース1着回数'] - df['1コース2着回数'])/df['1コース進入回数']
    #df['1コース差され率'] = df['1コース差され率'].fillna(0)
    df['選手登番'] = df['登番']
    df.drop(columns=['登番'], inplace=True)
    return df

USE_COLS = ['選手登番','性別','今期能力指数','前期能力指数','1着回数','2着回数','逃げ率','差し率','まくり率',
            '平均スタートタイミング','出走回数','複勝率','勝率','1コース1着回数','1コース2着回数','1コース3着回数',
            '2コース1着回数','2コース2着回数','2コース3着回数','3コース1着回数','3コース2着回数','3コース3着回数',
            '4コース1着回数','4コース2着回数','4コース3着回数','5コース1着回数','5コース2着回数','5コース3着回数',
            '6コース1着回数','6コース2着回数','6コース3着回数','1コースまくられ率']


def dataset(year, half):
    files = glob.glob(f"{CSV_DIR_B}B*")
    B_f_name = []
    for f in files:
        p = f'{CSV_DIR_B}' + 'B(\d{6}).csv'
        B_f_name.append(re.search(p,f).group(1))

    files = glob.glob(f"{CSV_DIR_K}K*")
    K_f_name = []
    for f in files:
        p = f'{CSV_DIR_K}'+'K(\d{6}).csv'
        K_f_name.append(re.search(p,f).group(1))
    
    B_df = read_csv(half_list(B_f_name, year, half), 'B')
    K_df = read_csv(half_list(K_f_name, year, half), 'K')
    R_df = get_racer_results(year, half).loc[:,USE_COLS]
    DF = pd.merge(B_df, K_df, on=['RaceID','選手登番'], how='inner')
    DF = pd.merge(DF, R_df, on='選手登番', how='inner')
    if '支部_lat' in DF.columns:
        DF = DF.drop(['支部_lat','支部_lng'],axis=1)
    DF = DF.astype({'選手登番':'int', 'RaceID':'int'})
    return DF

def get_dataset(frm=20):
    df = pd.DataFrame()
    for i in [i for i in range(frm, 25)]:
        for j in ['f','s']:
                a = dataset(i,j)
                df = pd.concat([df,a])
    return df.reset_index(drop=True)