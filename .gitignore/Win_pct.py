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

def graph_wpct_roster():
    roster = pd.read_csv("data/hawks_players_stats.csv")
    roster = roster[roster["GP"] >= 20].copy()
    roster = roster.sort_values("W_PCT", ascending=True).reset_index(drop=True)
    roster["NOM"] = roster["PLAYER_NAME"].apply(
        lambda n: n if len(n) <= 18
        else f"{n.split()[0][0]}. {' '.join(n.split()[1:])}"
    )
    roster["is_risa"] = roster["PLAYER_NAME"].str.contains(
        "Risacher", case=False
    )

    # Bilan équipe depuis le gamelog
    hawks = pd.read_csv("data/hawks_gamelog.csv")
    wpct_team = (hawks["WL"] == "W").mean() * 100

    # Couleurs — vert si au-dessus du bilan équipe, rouge sinon
    colors = []
    for _, row in roster.iterrows():
        if row["is_risa"]:
            colors.append(STYLE["accent"])
        elif row["W_PCT"] * 100 >= wpct_team:
            colors.append(STYLE["made"])
        else:
            colors.append(STYLE["missed"])

    N = len(roster)

    fig, ax = plt.subplots(figsize=(13, 9), facecolor=STYLE["bg"])
    fig.subplots_adjust(top=0.88, bottom=0.08,
                        left=0.22, right=0.88)
    ax.set_facecolor(STYLE["bg"])

    bars = ax.barh(
        roster["NOM"], roster["W_PCT"] * 100,
        color=colors, alpha=0.85,
        height=0.6, zorder=3
    )

    # Valeurs à droite
    for bar, (_, row) in zip(bars, roster.iterrows()):
        is_risa = row["is_risa"]
        ax.text(
            bar.get_width() + 0.8,
            bar.get_y() + bar.get_height() / 2,
            f"{row['W_PCT']*100:.1f}%  ·  "
            f"{int(row['W'])}V – {int(row['L'])}D  ·  "
            f"{int(row['GP'])} matchs",
            ha="left", va="center",
            fontsize=8.5 if is_risa else 8,
            color=STYLE["accent"] if is_risa else STYLE["muted"],
            fontweight="bold" if is_risa else "normal"
        )

    # ── Ligne bilan équipe — bien visible ─────────────────
    ax.axvline(wpct_team,
               color="#ffffff",
               linewidth=2.5,
               linestyle="-",
               alpha=0.6,
               zorder=5)

    # Label avec fond pour lisibilité
    ax.text(wpct_team + 0.8, N + 0.5,
            f"Bilan Hawks\n{wpct_team:.1f}%",
            fontsize=9, fontweight="bold",
            color="#ffffff",
            va="top", ha="left",
            bbox=dict(
                boxstyle="round,pad=0.35",
                facecolor=STYLE["surface"],
                edgecolor="#ffffff",
                linewidth=0.8,
                alpha=0.6
            ))

    # Rang de Risacher
    rank_risa = roster[roster["is_risa"]].index[0] + 1
    rank_top  = N - rank_risa + 1
    wpct_risa = roster[roster["is_risa"]]["W_PCT"].values[0] * 100

    # Axes
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"{int(v)}%")
    )
    ax.tick_params(axis="y", colors=STYLE["text"], labelsize=9.5)
    ax.tick_params(axis="x", colors=STYLE["dim"],  labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(STYLE["grid"])
        spine.set_linewidth(0.5)
    ax.grid(axis="x", color=STYLE["grid"],
            linewidth=0.4, alpha=0.5)
    ax.set_xlabel("% de victoires sur les matchs joués",
                  fontsize=9, color=STYLE["muted"], labelpad=8)

    # Légende — sans la ligne moyenne roster
    handles = [
        mpatches.Patch(color=STYLE["accent"],
                       label="Zaccharie Risacher"),
        mpatches.Patch(color=STYLE["made"],
                       label=f"Au-dessus bilan équipe ({wpct_team:.1f}%)"),
        mpatches.Patch(color=STYLE["missed"],
                       label=f"En-dessous bilan équipe ({wpct_team:.1f}%)"),
        plt.Line2D([0], [0], color="#ffffff",
                   linewidth=2.5, linestyle="-",
                   label=f"Bilan Hawks ({wpct_team:.1f}%)"),
    ]
    ax.legend(handles=handles,
              loc="lower right",
              frameon=True,
              facecolor=STYLE["surface"],
              edgecolor=STYLE["grid"],
              labelcolor=STYLE["muted"],
              fontsize=8.5)

    # Header & footer
    fig.text(0.5, 0.97,
             "Atlanta Hawks 2024-25 — % de victoires par joueur",
             ha="center", va="top",
             fontsize=17, fontweight="bold",
             color=STYLE["text"])
    fig.text(0.5, 0.935,
             f"Joueurs avec ≥ 20 matchs  ·  "
             f"Classé par W_PCT  ·  "
             f"Bilan Hawks : {wpct_team:.1f}%",
             ha="center", va="top",
             fontsize=10, color=STYLE["muted"])
    fig.text(0.5, 0.01,
             "nba_api · stats.nba.com  ·  "
             "W_PCT = % de victoires sur les matchs où le joueur a participé",
             ha="center", fontsize=7.5,
             color=STYLE["dim"], va="bottom")

    os.makedirs("plots", exist_ok=True)
    plt.savefig("plots/g6_wpct_roster.png",
                dpi=180, bbox_inches="tight",
                facecolor=STYLE["bg"])
    print("Sauvegardé : plots/g6_wpct_roster.png")
    plt.show()

graph_wpct_roster()