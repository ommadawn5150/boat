import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import json
from urllib.request import Request, urlopen 
from config import *
from download import *
from convert import *

import lightgbm as lgb

set_values(globals())

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
        

def get_data(date):
    DL_DATA(date, date, 'B')
    un_lzh(date, date, 'B')
    
def predict():
    model = lgb.Booster(model_file=f'../models/model_{FRM}.txt')
    