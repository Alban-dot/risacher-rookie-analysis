import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

STYLE = {
    "bg":      "#0a0e1a",
    "surface": "#111827",
    "grid":    "#1f2937",
    "text":    "#f9fafb",
    "muted":   "#9ca3af",
    "dim":     "#4b5563",
    "accent":  "#e8c547",
    "made":    "#4ade80",
    "missed":  "#f87171",
    "neutral": "#60a5fa",
}

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "text.color":       STYLE["text"],
    "figure.facecolor": STYLE["bg"],
    "axes.facecolor":   STYLE["bg"],
})

ALL_STAR_DATE = pd.Timestamp("2025-02-16")

def prepare_data(df, player_name="Zaccharie Risacher"):
    p = df[df["PLAYER_NAME"] == player_name].copy()

    p["GAME_DATE"] = pd.to_datetime(
        p["GAME_DATE"],
        format="%Y%m%d"
    )

    # Calcul des points
    p["POINTS"] = p.apply(
        lambda row: (
            3 if (
                row["SHOT_MADE_FLAG"] == 1
                and row["SHOT_TYPE"] == "3PT Field Goal"
            )
            else 2 if (
                row["SHOT_MADE_FLAG"] == 1
                and row["SHOT_TYPE"] == "2PT Field Goal"
            )
            else 0
        ),
        axis=1
    )

    par_match = (
        p.groupby("GAME_DATE")
        .agg(
            points=("POINTS", "sum"),
            tirs=("SHOT_MADE_FLAG", "count"),
            reussis=("SHOT_MADE_FLAG", "sum"),

            pts_2=(
                "POINTS",
                lambda x: x[
                    p.loc[x.index, "SHOT_TYPE"] == "2PT Field Goal"
                ].sum()
            ),

            pts_3=(
                "POINTS",
                lambda x: x[
                    p.loc[x.index, "SHOT_TYPE"] == "3PT Field Goal"
                ].sum()
            ),
        )
        .reset_index()
        .sort_values("GAME_DATE")
        .reset_index(drop=True)
    )

    par_match["match_num"] = range(1, len(par_match) + 1)

    par_match["pts_rolling"] = (
        par_match["points"]
        .ewm(span=10, min_periods=3)
        .mean()
    )

    par_match["mois"] = par_match["GAME_DATE"].dt.to_period("M")

    return par_match

def progression_points(df, player_name="Zaccharie Risacher"):
    par_match = prepare_data(df, player_name)

    N           = len(par_match)
    idx_allstar = par_match[
        par_match["GAME_DATE"] <= ALL_STAR_DATE
    ].index[-1]

    avant     = par_match[par_match["GAME_DATE"] <  ALL_STAR_DATE]
    apres     = par_match[par_match["GAME_DATE"] >= ALL_STAR_DATE]
    moy_avant = avant["points"].mean()
    moy_apres = apres["points"].mean()
    moy_saison= par_match["points"].mean()
    diff      = moy_apres - moy_avant

    fig, ax = plt.subplots(figsize=(16, 8), facecolor=STYLE["bg"])
    ax.set_facecolor(STYLE["bg"])

    x = par_match["match_num"].values

    # ── Barres empilées 2pts / 3pts ───────────────────────
    ax.bar(x, par_match["pts_2"],
           color=STYLE["made"], alpha=0.35,
           width=0.7, label="Points sur 2pts", zorder=2)
    ax.bar(x, par_match["pts_3"],
           bottom=par_match["pts_2"],
           color=STYLE["accent"], alpha=0.35,
           width=0.7, label="Points sur 3pts", zorder=2)

    # ── Zones avant / après All-Star ──────────────────────
    ax.axvspan(1, idx_allstar + 1,
               color=STYLE["neutral"], alpha=0.04, zorder=0)
    ax.axvspan(idx_allstar + 1, N,
               color=STYLE["accent"], alpha=0.04, zorder=0)

    # ── Ligne moyenne saison ──────────────────────────────
    ax.axhline(moy_saison,
               color=STYLE["dim"], linewidth=0.8,
               linestyle="--", alpha=0.7, zorder=3)
    ax.text(N + 0.5, moy_saison,
            f"Moy.\n{moy_saison:.1f} pts",
            fontsize=7.5, color=STYLE["dim"],
            va="center", ha="left")

    # ── Ligne All-Star ────────────────────────────────────
    ax.axvline(idx_allstar + 1,
               color=STYLE["muted"], linewidth=1.2,
               linestyle="--", alpha=0.7, zorder=3)
    ax.text(idx_allstar + 1.4, ax.get_ylim()[1]
            if ax.get_ylim()[1] > 0 else 35,
            "All-Star\nBreak",
            fontsize=8, color=STYLE["muted"],
            va="top", ha="left")

    # ── Courbe glissante ──────────────────────────────────
    mask = ~par_match["pts_rolling"].isna()
    ax.plot(x[mask], par_match["pts_rolling"].values[mask],
            color=STYLE["accent"], linewidth=2.8,
            zorder=5, label="Moy. glissante 10 matchs")

    # ── Annotations moyennes avant / après ────────────────
    mid_avant = (1 + idx_allstar) / 2
    mid_apres = (idx_allstar + N) / 2

    for mid, val, color, label in [
        (mid_avant, moy_avant, STYLE["neutral"],
         f"Avant All-Star\n{moy_avant:.1f} pts / match"),
        (mid_apres, moy_apres, STYLE["accent"],
         f"Après All-Star\n{moy_apres:.1f} pts / match"),
    ]:
        ax.text(mid, 2, label,
                ha="center", fontsize=9,
                color=color, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.4",
                          facecolor=STYLE["surface"],
                          edgecolor=color + "55",
                          linewidth=0.8))

    # ── Meilleur / pire match ─────────────────────────────
    best  = par_match.loc[par_match["points"].idxmax()]
    worst = par_match.loc[par_match["points"].idxmin()]

    for row_data, label, color, offset in [
    (best,  f"Meilleur\n{int(best['points'])} pts",  STYLE["made"],   +5),
    (worst, f"Pire\n{int(worst['points'])} pts",     STYLE["missed"], -5),
]:
        ax.annotate(
            label,
            xy=(row_data["match_num"], row_data["points"]),
            xytext=(row_data["match_num"], row_data["points"] + offset),
            fontsize=7.5, color=color,
            ha="center", va="center",
            arrowprops=dict(arrowstyle="-",
                        color=color, lw=0.8, alpha=0.6),
            bbox=dict(boxstyle="round,pad=0.3",
                  facecolor=STYLE["surface"],
                  edgecolor=color + "55",
                  linewidth=0.6)
    )

    # ── Séparateurs mensuels ──────────────────────────────
    mois_labels = par_match.groupby("mois")["match_num"].first()
    mois_noms   = {
        "2024-10": "Oct.", "2024-11": "Nov.", "2024-12": "Déc.",
        "2025-01": "Jan.", "2025-02": "Fév.", "2025-03": "Mar.",
        "2025-04": "Avr."
    }
    for mois, x_pos in mois_labels.items():
        ax.axvline(x_pos, color=STYLE["grid"],
                   linewidth=0.5, alpha=0.4, zorder=1)
        ax.text(x_pos + 0.3, 0.5,
                mois_noms.get(str(mois), str(mois)),
                fontsize=7.5, color=STYLE["dim"], va="bottom")

    # ── Axes ──────────────────────────────────────────────
    ax.set_xlim(0, N + 4)
    ax.set_ylim(0, par_match["points"].max() + 8)
    ax.set_xlabel("Numéro de match", fontsize=10,
                  color=STYLE["muted"], labelpad=8)
    ax.set_ylabel("Points marqués", fontsize=10,
                  color=STYLE["muted"], labelpad=8)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"{int(v)} pts")
    )
    ax.tick_params(colors=STYLE["dim"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(STYLE["grid"])
        spine.set_linewidth(0.5)
    ax.grid(axis="y", color=STYLE["grid"],
            linewidth=0.4, alpha=0.5)

    # ── Légende ───────────────────────────────────────────
    handles = [
        mpatches.Patch(color=STYLE["made"],   alpha=0.5,
                       label="Points sur tirs à 2pts"),
        mpatches.Patch(color=STYLE["accent"], alpha=0.5,
                       label="Points sur tirs à 3pts"),
        plt.Line2D([0], [0], color=STYLE["accent"],
           linewidth=2.5,
           label="Lissage exponentiel (span=10)"),
    ]
    ax.legend(handles=handles, loc="upper left",
              frameon=True, facecolor=STYLE["surface"],
              edgecolor=STYLE["grid"],
              labelcolor=STYLE["muted"], fontsize=8.5)

    # ── Header ────────────────────────────────────────────
    fig.text(0.5, 0.97,
             "Zaccharie Risacher — Points par match 2024-25",
             ha="center", va="top",
             fontsize=17, fontweight="bold",
             color=STYLE["text"])
    fig.text(0.5, 0.935,
             f"75 matchs  ·  Hors lancers francs  ·  "
             f"Avant All-Star : {moy_avant:.1f} pts  →  "
             f"Après All-Star : {moy_apres:.1f} pts",
             ha="center", va="top",
             fontsize=10, color=STYLE["muted"])
    fig.text(0.5, 0.01,
             "nba_api · stats.nba.com  ·  "
             "* Points calculés sans lancers francs",
             ha="center", fontsize=7.5,
             color=STYLE["dim"], va="bottom")

    plt.tight_layout(rect=[0, 0.02, 1, 0.92])

    os.makedirs("plots", exist_ok=True)
    plt.savefig("plots/risacher_progression_points.png",
                dpi=180, bbox_inches="tight",
                facecolor=STYLE["bg"])
    print("Sauvegardé : plots/risacher_progression_points.png")
    plt.show()

# ── Lancement ─────────────────────────────────────────────
df = pd.read_csv("nba_shots_2024_25.csv")
progression_points(df)