import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import re
import lhafile

import config
gl = globals()
config.set_values(gl)

def mk_racer_csv(FILE_NAME):
    with open(RACER_TXT + FILE_NAME + '.txt', encoding='shift-jis') as f:
        data = f.readlines()
    return data

def txt_to_csv(data):
    for i in data:
        clip_text = i[21:37]
        print(clip_text)

files = glob.glob(RACER_LZH + "fan*.lzh")
for i in files:
    file = lhafile.Lhafile(i)
    info = file.infolist()
    name = info[0].filename
    print(RACER_TXT + name)

    with open(RACER_TXT + name , "wb") as f:
        f.write(file.read(name))
        
files = glob.glob(RACER_TXT + "fan*.txt")
f_name = []
for f in files:
    p = r'fan\d{4}'
    f_name.append(re.search(p,f).group(0))

b_len = [4,16,15,4,2,1,6,1,2,3,2,2,4,4,3,3,3,2,2,3,3,4,3,3,3,4,3,3,3,4,3,3,3,4,3,3,3,4,3,3,3,4,3,3,2,2,2,4,4,4,1,8,8,3,3,3,3,3,3,3,2,2,2,2,2,2,2,2,3,3,3,3,3,3,2,2,2,2,2,2,2,2,3,3,3,3,3,3,2,2,2,2,2,2,2,2,3,3,3,3,3,3,2,2,2,2,2,2,2,2,3,3,3,3,3,3,2,2,2,2,2,2,2,2,3,3,3,3,3,3,2,2,2,2,2,2,2,2,2,2,2,2,6]
col_name = ['登番','名前漢字','名前カナ','支部','級','年号','生年月日','性別','年齢','身長','体重','血液型','勝率','複勝率','1着回数','2着回数','出走回数','優出回数','優勝回数','平均スタートタイミング','1コース進入回数','1コース複勝率','1コース平均スタートタイミング','1コース平均スタート順位','2コース進入回数','2コース複勝率','2コース平均スタートタイミング','2コース平均スタート順位','3コース進入回数','3コース複勝率','3コース平均スタートタイミング','3コース平均スタート順位','4コース進入回数','4コース複勝率','4コース平均スタートタイミング','4コース平均スタート順位','5コース進入回数','5コース複勝率','5コース平均スタートタイミング','5コース平均スタート順位','6コース進入回数','6コース複勝率','6コース平均スタートタイミング','6コース平均スタート順位','前期級','前々期級','前々々期級','前期能力指数','今期能力指数','年','期','算出期間（自）','算出期間（至）','養成期','1コース1着回数','1コース2着回数','1コース3着回数','1コース4着回数','1コース5着回数','1コース6着回数','1コースF回数','1コースL0回数','1コースL1回数','1コースK0回数','1コースK1回数','1コースS0回数','1コースS1回数','1コースS2回数','2コース1着回数','2コース2着回数','2コース3着回数','2コース4着回数','2コース5着回数','2コース6着回数','2コースF回数','2コースL0回数','2コースL1回数','2コースK0回数','2コースK1回数','2コースS0回数','2コースS1回数','2コースS2回数','3コース1着回数','3コース2着回数','3コース3着回数','3コース4着回数','3コース5着回数','3コース6着回数','3コースF回数','3コースL0回数','3コースL1回数','3コースK0回数','3コースK1回数','3コースS0回数','3コースS1回数','3コースS2回数','4コース1着回数','4コース2着回数','4コース3着回数','4コース4着回数','4コース5着回数','4コース6着回数','4コースF回数','4コースL0回数','4コースL1回数','4コースK0回数','4コースK1回数','4コースS0回数','4コースS1回数','4コースS2回数','5コース1着回数','5コース2着回数','5コース3着回数','5コース4着回数','5コース5着回数','5コース6着回数','5コースF回数','5コースL0回数','5コースL1回数','5コースK0回数','5コースK1回数','5コースS0回数','5コースS1回数','5コースS2回数','6コース1着回数','6コース2着回数','6コース3着回数','6コース4着回数','6コース5着回数','6コース6着回数','6コースF回数','6コースL0回数','6コースL1回数','6コースK0回数','6コースK1回数','6コースS0回数','6コースS1回数','6コースS2回数','コースなしL0回数','コースなしL1回数','コースなしK0回数','コースなしK1回数','出身地']

for j in ['fan1704','fan1610','fan1604','fan1510','fan1504','fan1410']:
    print(j)
    a = mk_racer_csv(j)
    a.remove('\n')
    df = pd.DataFrame(columns=col_name)
    for i in range(len(a)):
        c = 0
        list = []
        
        for l in b_len:
            t = a[i].encode('shift-jis')[c:c+l].decode('shift-jis').replace('\u3000','').replace(' ','')
            c = c + l
            list.append(t)
        list = [list]
        temp = pd.DataFrame(list,columns=col_name)
        df = pd.concat([df,temp]).reset_index(drop=True)
    df.to_csv(RACER_CSV + str(j) + '.csv',index=False)