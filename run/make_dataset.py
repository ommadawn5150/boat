import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import json
import sys

dirname = os.path.dirname(__file__)
sys.path.append(os.path.join(dirname, '..'))
sys.path.append(os.path.join(dirname, '../boat/'))
from data_loader import *
import pickle
frm = 17
df = get_dataset(frm)
print(df.info())
with open(f'./data/pickle/df{frm}.pkl', 'wb') as f:
    pickle.dump(df, f)