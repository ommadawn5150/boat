"""
Discord Bot for boat racing predictions.

Setup:
  pip install discord.py

Required environment variable (or set in config.json):
  DISCORD_BOT_TOKEN  — Bot token from Discord Developer Portal

Slash commands:
  /yoso            — 本日の全予想を表示
  /yoso 江戸川 3   — 特定会場・レース番号の予想を表示
  /seiseki         — 直近30日のROI・的中率を表示
"""

import os
import sys
import discord
from discord import app_commands
import pandas as pd
from datetime import datetime as dt, timedelta as td

sys.path.append('../')
sys.path.append('../boat/')

from config import *
set_values(globals())

HISTORY_PATH = '../pred/history.csv'
RESULT_PATH_TEMPLATE = '../data/csv/K_files/K{date}.csv'

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def load_history(days: int = 30) -> pd.DataFrame:
    if not os.path.exists(HISTORY_PATH):
        return pd.DataFrame()
    df = pd.read_csv(HISTORY_PATH)
    cutoff = (dt.now() - td(days=days)).strftime('%y%m%d')
    return df[df['date'] >= cutoff]


def calc_roi(history: pd.DataFrame) -> dict:
    """Kファイルの払戻データと予想履歴をJoinしてROIを計算する。"""
    if history.empty:
        return {'races': 0, 'hits': 0, 'roi': None}

    bets = history[history['buy']].copy()
    if bets.empty:
        return {'races': 0, 'hits': 0, 'roi': None}

    results = []
    for _, row in bets.iterrows():
        k_path = RESULT_PATH_TEMPLATE.format(date=row['date'])
        if not os.path.exists(k_path):
            continue
        kdf = pd.read_csv(k_path, usecols=['RaceID', '3連単_結果', '3連単_払戻'])
        race_result = kdf[kdf['RaceID'] == row['RaceID']]
        if race_result.empty:
            continue
        actual = str(race_result['3連単_結果'].values[0])
        payout = race_result['3連単_払戻'].values[0]
        kaime_list = row['kaime'].split('|')
        hit = actual in kaime_list
        results.append({'hit': hit, 'payout': float(payout) if hit else 0})

    if not results:
        return {'races': len(bets), 'hits': 0, 'roi': None}

    total_bet = len(results) * len(bets['kaime'].iloc[0].split('|')) * 100  # 100円×買い目数
    total_return = sum(r['payout'] for r in results)
    hits = sum(r['hit'] for r in results)
    roi = (total_return - total_bet) / total_bet * 100 if total_bet > 0 else None
    return {'races': len(results), 'hits': hits, 'roi': roi}


def get_today_predictions(place_name: str = None, race_no: int = None) -> str:
    if not os.path.exists(HISTORY_PATH):
        return '予想履歴が見つかりません。先に predictor.py を実行してください。'

    today = dt.now().strftime('%y%m%d')
    df = pd.read_csv(HISTORY_PATH)
    today_df = df[(df['date'] == int(today)) & df['buy']]

    if place_name:
        today_df = today_df[today_df['place'] == place_name]
    if race_no:
        today_df = today_df[today_df['R'] == race_no]

    if today_df.empty:
        return '本日の買い目対象レースはありません。'

    lines = [f'## {today} 予想']
    for _, row in today_df.iterrows():
        kaime_list = row['kaime'].split('|')
        lines.append(f"### {row['place']} {row['R']}R : {row['pred_rank']}")
        lines.append(f"**買い目** : {', '.join(kaime_list)}")

    return '\n'.join(lines)


@tree.command(name='yoso', description='本日の予想を表示します。会場名とレース番号でフィルターできます。')
@app_commands.describe(place='会場名（例：江戸川）', race='レース番号（例：3）')
async def yoso(interaction: discord.Interaction, place: str = None, race: int = None):
    await interaction.response.defer()
    msg = get_today_predictions(place_name=place, race_no=race)
    # Discordの2000文字制限に対応
    if len(msg) > 1900:
        for chunk in [msg[i:i+1900] for i in range(0, len(msg), 1900)]:
            await interaction.followup.send(chunk)
    else:
        await interaction.followup.send(msg)


@tree.command(name='seiseki', description='直近30日間のROI・的中率を表示します。')
async def seiseki(interaction: discord.Interaction):
    await interaction.response.defer()
    history = load_history(days=30)
    result = calc_roi(history)

    if result['races'] == 0:
        await interaction.followup.send('過去30日間の買い目データがありません。')
        return

    roi_str = f"{result['roi']:.1f}%" if result['roi'] is not None else '計算中'
    hit_rate = result['hits'] / result['races'] * 100 if result['races'] > 0 else 0
    msg = (
        f'## 直近30日間の成績\n'
        f'対象レース数: **{result["races"]}**\n'
        f'的中数: **{result["hits"]}**\n'
        f'的中率: **{hit_rate:.1f}%**\n'
        f'ROI: **{roi_str}**'
    )
    await interaction.followup.send(msg)


@client.event
async def on_ready():
    await tree.sync()
    print(f'Bot ready: {client.user}')


if __name__ == '__main__':
    token = os.environ.get('DISCORD_BOT_TOKEN', '')
    if not token:
        print('エラー: 環境変数 DISCORD_BOT_TOKEN が設定されていません。')
        print('  export DISCORD_BOT_TOKEN="your_token_here"')
        sys.exit(1)
    client.run(token)
