import glob
import re
import pandas as pd
from argparse import ArgumentParser
import shutil
from tqdm import tqdm
import json
from geopy.geocoders import Nominatim
from multiprocessing import Pool
import os

import config
gl = globals()
config.set_values(gl)


def get_option():
    argparser = ArgumentParser()
    argparser.add_argument('-b', '--bangumi', action='store_true',
                            help='Make bangumi csv')
    argparser.add_argument('-k', '--kekka', action='store_true',
                            help='Make kekka csv')
    argparser.add_argument('-i', '--info', action='store_true',
                            help='Make raceinfo json')
    return argparser.parse_args()

def mkcsv_k(FILE_NAME):
    def try_int(x, col):
        if col in ['着','モーター', 'ボート', '進入']:
            try:
                if col == '着' and int(x) == 0:
                    return 6
                else:
                    return int(x)
            except:
                if col == '着':
                    return 6
                else:
                    return 0
        elif col in ['スタートタイミング', '展示']:
            try:
                return float(x)
            except:
                return 0
        else:
            return x
    
    place_code = {'桐生':'01','戸田':'02','江戸川':'03','平和島':'04','多摩川':'05','浜名湖':'06','蒲郡':'07','常滑':'08','津':'09','三国':'10','びわこ':'11','琵琶湖':'11','住之江':'12','尼崎':'13','鳴門':'14','丸亀':'15','児島':'16','宮島':'17','徳山':'18','下関':'19','若松':'20','芦屋':'21','福岡':'22','唐津':'23','大村':'24'}

    with open(SAVE_DIR_K_TXT + FILE_NAME + '.TXT') as f:
        data = f.readlines()
    date = FILE_NAME[1:7]
    races = pd.DataFrame()
    for n,i in enumerate(data):
        if '払戻金' in i: continue
        if "単勝" in i:
            tansho = i.replace('\u3000', '').split()[1:]
            
        if "２連単" in i:
            nirentan = i.replace('人気','').replace('\u3000', '').split()[1:]
        if "３連単" in i:
            sanrentan = i.replace('人気','').replace('\u3000', '').split()[1:]
        
        if '［成績］' in i:
            place = i.replace('\u3000', '').split()[0].replace('［成績］', '')
            place = place_code[place]
        
        if i == '-------------------------------------------------------------------------------\n':
            R = f"{data[n-2].split()[0].replace('R', '').zfill(2)}"
            
            race = data[n+1 : n+7]
            race = [i.replace('\u3000', '').split()[:9] for i in race]
            race = pd.DataFrame(race, columns=['着', '艇番', '選手登番', '選手名', 'モーター', 'ボート', '展示', '進入', 'スタートタイミング '])
            
            race['R'] = R
            race['場所'] = place
            race['日時'] = f'20{date[:2]}_{int(date[2:4])}_{int(date[4:6])}'
            race['RaceID'] = int(f'20{date}{place}{R}')
        
        if '３連複' in i :
            if len(tansho) == 2:
                race['単勝_結果'] = tansho[0]
                race['単勝_払戻'] = tansho[1]
            else:
                race['単勝_結果'] = 0
                race['単勝_払戻'] = 0
            
            if len(nirentan) == 3:
                race['2連単_結果'] = nirentan[0]
                race['2連単_払戻'] = nirentan[1]
                race['2連単_人気'] = nirentan[2]
            else:
                race['2連単_結果'] = 0
                race['2連単_払戻'] = 0
                race['2連単_人気'] = 0
            
            if len(sanrentan) == 3:
                race['3連単_結果'] = sanrentan[0]
                race['3連単_払戻'] = sanrentan[1]
                race['3連単_人気'] = sanrentan[2]
            else:
                race['3連単_結果'] = 0
                race['3連単_払戻'] = 0
                race['3連単_人気'] = 0

            for col in race.columns:
                race[col] = race[col].apply(lambda x: try_int(x, col))
            
            races = pd.concat([races, race])
    
    races.to_csv(f'{CSV_DIR_K}{FILE_NAME}.csv', index=False)
    shutil.move(SAVE_DIR_K_TXT + FILE_NAME + '.TXT', SAVE_DIR_K_CONVERTED + FILE_NAME + '.TXT')


def mkcsv_b(FILE_NAME):
    with open(SAVE_DIR_B_TXT + FILE_NAME + '.TXT')as f:
        data = f.readlines()
    import re

    racers = [row.replace('\u3000','').replace('\n','') for row in data if re.match('^[1-6]\s\d+[^0-9]+\d{2}[^0-9]+\d{2}[AB]\d\s', row)]
    pattern = '^([1-6])\s+(\d+)([^0-9]+)(\d{2})([^0-9]+)(\d{2})([AB]\d{1})\s*(\d+\.\d{2})\s*(\d+\.\d{2})\s*(\d+\.\d{2})\s*(\d+\.\d+)\s*\d+\s*(\d+\.\d{2})\s*\d+\s*(\d+\.\d{2})\s(.)(.)(.)(.)(.)(.)(.)(.)(.)(.)(.)(.)'
    pattern_re = re.compile(pattern)

    values = [re.match(pattern_re, racer).groups() for racer in racers]
    import pandas as pd

    column = ['艇番', '選手登番', '選手名', '年齢', '支部', '体重', '級別', '全国勝率', '全国2連率', '当地勝率', '当地2連率', 'モーター2連率', 'ボート2連率','今節成績11','今節成績12','今節成績21','今節成績22','今節成績31','今節成績32','今節成績41','今節成績42','今節成績51','今節成績52','今節成績61','今節成績62']
    df = pd.DataFrame(values, columns=column)
    races = [row.replace('\u3000','').replace('\n','').replace(' ','') for row in data if re.match('^\s{3}[^0-9\s]', row)]
    import unicodedata
    races_uni = [unicodedata.normalize('NFKC', i) for i in races]
    place_code = {'桐生':'01','戸田':'02','江戸川':'03','平和島':'04','多摩川':'05','浜名湖':'06','蒲郡':'07','常滑':'08','津':'09','三国':'10','びわこ':'11','琵琶湖':'11','住之江':'12','尼崎':'13','鳴門':'14','丸亀':'15','児島':'16','宮島':'17','徳山':'18','下関':'19','若松':'20','芦屋':'21','福岡':'22','唐津':'23','大村':'24'}
    class_mapping = {'B2':1,'B1':2,'A2':3,'A1':4}


    pattern = re.compile('^.+\d+日(\d{4})年(\d+)月(\d+)日ボートレース(.+)')
    racers_repp = list([re.match(pattern, i).groups() for i in races_uni])

    racers_reppp = []
    pl =[]
    for i in racers_repp:
        for j, k in place_code.items():
            if i[3] == j:
                racers_reppp.append(f'{int(i[0]):02}' + f'{int(i[1]):02}' + f'{int(i[2]):02}' + f'{int(k):02}')
                pl.append(k)
            else:
                pass

    racers_rep_R =[]
    R = []
    for i in racers_reppp:
        for r in range(12):
            racers_rep_R.append(i + f'{int(r+1):02}')
            R.append(f'{int(r + 1):02}')

    df['RaceID'] = 0
    df['場所'] = 0
    df['R'] = 0

    raceID = []
    Rs = []
    pls = []
    for i in range(df.shape[0]):
        raceID.append(racers_rep_R[i//6])
        Rs.append(R[i//6])
        pls.append(pl[i//72])
    df['RaceID'] = raceID
    df['R'] = Rs
    df['場所'] = pls

    for col in df.columns:
        if '今節成績' in col:
            df[col] = df[col].apply(lambda x: 0 if x == ' ' else x)
    
    obj_cols = []
    for i in df.columns:
        if df[i].dtype == object:
            obj_cols.append(i)
    seiseki = {
        'F' : -20,
        'S' : -15,
        'K' : -10,
        'L' : 20,
        '0' : 0,
        '1' : 1,
        '2' : 2,
        '3' : 3,
        '4' : 4,
        '5' : 5,
        '6' : 6,
    }
    df_pp = df.copy()
    for i in obj_cols:
        if '今節成績' in i:
            df_pp[i] = df.copy()[i].apply(lambda x: seiseki[str(x)])
        
        if i == '級別':
            class_mapping = {'B2':1,'B1':2,'A2':3,'A1':4}
            df_pp['級別'] = df.copy()['級別'].map(class_mapping)
    
    #sibu_dict = {}
    #for i in df['支部'].unique():
    #    sibu_dict[i] = geo_sibu(i)

    #df_pp['支部_lat'] = df.copy()['支部'].apply(lambda x: sibu_dict[x][1])
    #df_pp['支部_lng'] = df.copy()['支部'].apply(lambda x: sibu_dict[x][2])
    df_pp = df_pp.drop(['選手名','支部'],axis=1)

    df_pp.to_csv(CSV_DIR_B + FILE_NAME +  '.csv')
    shutil.move(SAVE_DIR_B_TXT + FILE_NAME + '.TXT', SAVE_DIR_B_CONVERTED+ FILE_NAME + '.TXT')


def mkrcinfo(FILE_NAME):
    with open(SAVE_DIR_K_TXT + FILE_NAME + '.TXT') as f:
        data = f.readlines()

    prize_dict = {}
    place_code = {'桐生':'01','戸田':'02','江戸川':'03','平和島':'04','多摩川':'05','浜名湖':'06','蒲郡':'07','常滑':'08','津':'09','三国':'10','びわこ':'11','琵琶湖':'11','住之江':'12','尼崎':'13','鳴門':'14','丸亀':'15','児島':'16','宮島':'17','徳山':'18','下関':'19','若松':'20','芦屋':'21','福岡':'22','唐津':'23','大村':'24'}

    for i in data:
        if re.match('^\s{3}第.+日', i):
            place =(i.replace('\u3000','').replace('\n','').replace('/','_').replace('_ ', '_'))
            pattern_place = re.compile('^.+(\d{4}_.+\d+)\s.+ボートレース([^0-9A-Z\s-]+)')
            a = re.match(pattern_place, place).groups()
            b = a[0].split('_')
            raceid_ = b[0] + f'{int(b[1]):02}' + f'{int(b[2]):02}' + place_code[a[1]]
            

        
        if re.match('^\s{10}[1\s]\dR',i):
            try:
                prize =(i.replace('\u3000','').replace('\n','').replace('/','_').replace('_ ', '_'))
                pattern_place = re.compile('^\s{10}([1\s]\dR)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)')
                a = re.match(pattern_place, prize).groups()
                raceid = int(raceid_ + a[0].replace('R','').replace(' ','0'))

                tmp = {'3連単' : {}, '3連複' : {}, '2連単' : {}, '2連複' : {}, '単勝' : {}}
                tmp['3連単']['result'] = a[1]
                tmp['3連単']['prize'] = a[2]
                tmp['3連複']['result'] = a[3]
                tmp['3連複']['prize'] = a[4]
                tmp['2連単']['result'] = a[5]
                tmp['2連単']['prize'] = a[6]
                tmp['2連複']['result'] = a[7]
                tmp['2連複']['prize'] = a[8]
                prize_dict[raceid] = tmp
                
                count = 0
            except Exception as e:
                pass
                #print(i)
        
        if '単勝' in i:
            try :
                prize =(i.replace('\u3000','').replace('\n','').replace('/','_').replace('_ ', '_'))
                pattern_place = re.compile('^\s{8}単勝\s+(\d+)\s+(\d+)')
                a = re.match(pattern_place, prize).groups()
                count += 1
                raceid = int(raceid_ + f'{int(count):02}')
                
                d = {'result' : '', 'prize' : ''}
                d['result'] = a[0]
                d['prize'] = a[1]
                prize_dict[raceid]['単勝'] = d
                
            except Exception as e:
                pass
                #print(i)
    with open(DIR_RACE_INFO + FILE_NAME +  '.json','w') as f:
        json.dump(prize_dict, f,ensure_ascii=False, indent=4, sort_keys=False, separators=(',', ': '))


if __name__ == '__main__':
    args = get_option()
    print(args)
    if args.info :
        files = glob.glob(f"{SAVE_DIR_K_TXT}K*")
        f_name = []
        for f in files:
            p = SAVE_DIR_K_TXT + '(K\d{6}).TXT'
            f_name.append(re.search(p,f).group(1)) 

        for f in tqdm(f_name):
            mkrcinfo(f)

    if args.kekka :
        files = glob.glob(f"{SAVE_DIR_K_TXT}K*")
        f_name = []
        for f in files:
            p = SAVE_DIR_K_TXT + '(K\d{6}).TXT'
            f_name.append(re.search(p,f).group(1)) 

        for f in tqdm(f_name):
            #mkrcinfo(f)
            mkcsv_k(f)


    if args.bangumi :
        files = glob.glob(f"{SAVE_DIR_B_TXT}B*")
        f_name = []
        for f in files:
            p = SAVE_DIR_B_TXT + '(B\d{6}).TXT'
            f_name.append(re.search(p,f).group(1))
        for f in tqdm(f_name):
            mkcsv_b(f)
        #Jwith Pool() as p:
        #    list(tqdm(p.imap(mkcsv_b, f_name), total=len(f_name)))

