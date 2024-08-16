from time import sleep
from requests import get
from datetime import datetime as dt
from datetime import timedelta as td
from os import makedirs
from tqdm import tqdm
import re
import lhafile
import os
import shutil
import json
import codecs
from argparse import ArgumentParser

import config
gl = globals()
config.set_values(gl)

def get_option(START_DATE, END_DATE):
    argparser = ArgumentParser()
    argparser.add_argument('-dl', '--download', action='store_true',
                            help='Download files')
    argparser.add_argument('-u', '--unlzh', action='store_true',
                            help='Unlzh lzh files')
    argparser.add_argument('-s', '--start', type=str,
                            default=START_DATE,
                            help='Start dat')
    argparser.add_argument('-e', '--end', type=str,
                            default=END_DATE,
                            help='End date')
    argparser.add_argument('-bk', '--boat_kind', type=str,
                            default='KB',
                            help='Boat Kind')
    return argparser.parse_args()

def DL_DATA(START_DATE, END_DATE, BK):
    if BK == 'K':
        SAVE_DIR = SAVE_DIR_K
        FIXED_URL = FIXED_URL_K
        BK = 'k'
    elif BK == 'B':
        SAVE_DIR = SAVE_DIR_B
        FIXED_URL = FIXED_URL_B
        BK = 'b'
    else :
        print("Invalid BK")
        return False
    try:
        print("Starting Download")
        makedirs(SAVE_DIR, exist_ok=True)
        start_date = dt.strptime(START_DATE, '%Y-%m-%d')
        end_date = dt.strptime(END_DATE, '%Y-%m-%d')
        days_num = (end_date - start_date).days + 1
        date_list = []
        for i in range(days_num):
            target_date = start_date + td(days=i)
            date_list.append(target_date.strftime("%Y%m%d"))
        for date in tqdm(date_list):
            yyyymm = date[0:4] + date[4:6]
            yymmdd = date[2:4] + date[4:6] + date[6:8]
            variable_url = FIXED_URL + yyyymm + "/"+ BK + yymmdd + ".lzh"
            file_name = BK + yymmdd + ".lzh"
            r = get(variable_url)
            if r.status_code == 200:
                f = open(SAVE_DIR + file_name, 'wb')
                f.write(r.content)
                f.close()
            else:
                print(f'Failed to download {date} file.')
            sleep(INTERVAL)
    except Exception as e:
        print(e)

def un_lzh(BK):
    if BK == 'K':
        SAVE_DIR = SAVE_DIR_K
        SAVE_DIR_UNLZH = SAVE_DIR_K_UNLZH
        SAVE_DIR_TXT = SAVE_DIR_K_TXT
    elif BK == 'B' :
        SAVE_DIR = SAVE_DIR_B
        SAVE_DIR_UNLZH = SAVE_DIR_B_UNLZH
        SAVE_DIR_TXT = SAVE_DIR_B_TXT
    else :
        print("Invalid BK")
        return False
    
    lzh_file_list = os.listdir(SAVE_DIR)
    
    for lzh_file_name in tqdm(lzh_file_list):
        if re.search(".lzh", lzh_file_name):

            file = lhafile.Lhafile(SAVE_DIR + lzh_file_name)

            info = file.infolist()
            name = info[0].filename

            with open("./data/" + name, "wb") as f:
                f.write(file.read(name))

            sf = codecs.open("./data/" + name, 'r', encoding='shift-jis')
            uf = codecs.open(SAVE_DIR_TXT + name, 'w', encoding='utf-8')
            for line in sf:
                uf.write(line)
            sf.close()
            uf.close()
            os.remove("./data/" + name)
            shutil.move(SAVE_DIR + lzh_file_name , SAVE_DIR_UNLZH + lzh_file_name)


if __name__ == '__main__':
    END_DATE = dt.today().strftime("%Y-%m-%d")
    START_DATE = (dt.today() - td(days=7)).strftime("%Y-%m-%d")
    args = get_option(START_DATE, END_DATE)
    if args.download == True :
        if len(args.start) > 0:
            START_DATE = args.start
        if len(args.end) > 0:
            END_DATE = args.end
        
        try:
            if args.boat_kind == 'BK':
                DL_DATA(START_DATE, END_DATE, "K")
                DL_DATA(START_DATE, END_DATE, "B")
            elif args.boat_kind == 'K':
                DL_DATA(START_DATE, END_DATE, "K")
            elif args.boat_kind == 'B':
                DL_DATA(START_DATE, END_DATE, "B")
            else:
                print("Invalid boat_kind")
        except Exception as e:
            print(e)

    if args.unlzh:
        if args.boat_kind == 'BK':
            un_lzh("B")
            un_lzh("K")
        elif args.boat_kind == 'K':
            un_lzh("K")
        elif args.boat_kind == 'B':
            un_lzh("B")
        else:
            print("Invalid boat_kind")