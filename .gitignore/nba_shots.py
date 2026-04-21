import time
import pandas as pd
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.static import players, teams

# --- Configuration ---
SEASON = "2024-25"
SEASON_TYPE = "Regular Season"  # ou "Playoffs"
OUTPUT_FILE = "nba_shots_2024_25.csv"

# --- Récupère tous les joueurs actifs ---
all_players = players.get_active_players()
print(f"{len(all_players)} joueurs actifs trouvés")

all_shots = []
errors = []

for i, player in enumerate(all_players):
    player_id = player["id"]
    player_name = player["full_name"]
    print(f"[{i+1}/{len(all_players)}] {player_name}...")

    try:
        shotlog = shotchartdetail.ShotChartDetail(
            team_id=0,
            player_id=player_id,
            season_nullable=SEASON,
            season_type_all_star=SEASON_TYPE,
            context_measure_simple="FGA"
        )
        df = shotlog.get_data_frames()[0]

        if not df.empty:
            df["PLAYER_NAME"] = player_name
            all_shots.append(df)
            print(f"  → {len(df)} tirs récupérés")
        else:
            print(f"  → Aucun tir")

    except Exception as e:
        print(f"  ⚠️ Erreur : {e}")
        errors.append(player_name)

    time.sleep(0.8)  # Important pour ne pas se faire bloquer

# --- Sauvegarde ---
final_df = pd.concat(all_shots, ignore_index=True)
final_df.to_csv(OUTPUT_FILE, index=False)
print(f"\n✅ Terminé ! {len(final_df)} tirs sauvegardés dans '{OUTPUT_FILE}'")

if errors:
    print(f"⚠️ Erreurs sur : {errors}")