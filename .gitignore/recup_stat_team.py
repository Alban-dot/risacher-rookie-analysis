import pandas as pd
import time
import os
from nba_api.stats.endpoints import (
    leaguedashplayerstats,
    teamgamelog,
    playergamelog
)
from nba_api.stats.static import teams, players

os.makedirs("data",  exist_ok=True)  
os.makedirs("plots", exist_ok=True)

SEASON   = "2024-25"
HAWKS_ID = [t["id"] for t in teams.get_teams()
            if t["abbreviation"] == "ATL"][0]

# ── 1. Stats saison de tous les Hawks ─────────────────────
print("Récupération stats joueurs Hawks...")
hawk_stats = leaguedashplayerstats.LeagueDashPlayerStats(
    season=SEASON,
    season_type_all_star="Regular Season",
    team_id_nullable=HAWKS_ID
).get_data_frames()[0]

hawk_stats.to_csv("data/hawks_players_stats.csv", index=False)
print(f"  {len(hawk_stats)} joueurs · colonnes : {list(hawk_stats.columns)}")
time.sleep(1)

# ── 2. Game log de l'équipe (stats par match) ─────────────
print("Récupération game log Hawks...")
hawks_games = teamgamelog.TeamGameLog(
    team_id=HAWKS_ID,
    season=SEASON,
    season_type_all_star="Regular Season"
).get_data_frames()[0]

hawks_games.to_csv("data/hawks_gamelog.csv", index=False)
print(f"  {len(hawks_games)} matchs · colonnes : {list(hawks_games.columns)}")
time.sleep(1)

# ── 3. Game log de Risacher (stats par match) ─────────────
print("Récupération game log Risacher...")
from nba_api.stats.static import players
risa_id = [p["id"] for p in players.get_players()
           if p["full_name"] == "Zaccharie Risacher"][0]
print(f"  ID Risacher : {risa_id}")

risa_games = playergamelog.PlayerGameLog(
    player_id=risa_id,
    season=SEASON,
    season_type_all_star="Regular Season"
).get_data_frames()[0]

risa_games.to_csv("data/risacher_gamelog.csv", index=False)
print(f"  {len(risa_games)} matchs")
print(risa_games[["GAME_DATE","PTS","FGM","FGA","FG_PCT",
                   "FG3M","FG3A","MIN"]].head())