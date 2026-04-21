import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

# ── Design system ─────────────────────────────────────────
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
MOIS_NOMS = {
    "2024-10": "Oct.", "2024-11": "Nov.", "2024-12": "Déc.",
    "2025-01": "Jan.", "2025-02": "Fév.", "2025-03": "Mar.",
    "2025-04": "Avr."
}

# ── Chargement données (commun à tous) ────────────────────
def load_data():
    risa = pd.read_csv("data/risacher_gamelog.csv")
    risa["GAME_DATE"] = pd.to_datetime(
        risa["GAME_DATE"], format="%b %d, %Y"
    )
    risa = (risa
            .sort_values("GAME_DATE")
            .drop_duplicates(subset="GAME_DATE", keep="first")
            .reset_index(drop=True))
    risa["MATCH_NUM"] = range(1, len(risa) + 1)
    risa["MOIS"]      = risa["GAME_DATE"].dt.to_period("M")
    risa["PERIODE"]   = risa["GAME_DATE"].apply(
        lambda d: "après" if d >= ALL_STAR_DATE else "avant"
    )

    hawks = pd.read_csv("data/hawks_gamelog.csv")
    hawks["GAME_DATE"] = pd.to_datetime(
        hawks["GAME_DATE"], format="%b %d, %Y"
    )
    hawks = (hawks
             .sort_values("GAME_DATE")
             .drop_duplicates(subset="GAME_DATE", keep="first")
             .reset_index(drop=True))

    roster = pd.read_csv("data/hawks_players_stats.csv")

    merged = risa.merge(
        hawks[["GAME_DATE", "PTS", "FGA", "FGM", "FG_PCT"]],
        on="GAME_DATE", how="inner",
        suffixes=("_risa", "_hawks")
    )
    merged["pct_pts"]       = merged["PTS_risa"] / merged["PTS_hawks"] * 100
    merged["usage"]         = merged["FGA_risa"] / merged["FGA_hawks"] * 100
    merged["pts_rolling"] = merged["PTS_risa"].ewm(span=10, min_periods=3).mean()
    merged["usage_rolling"] = merged["usage"].rolling(10, min_periods=3).mean()
    merged["pct_rolling"]   = merged["pct_pts"].rolling(10, min_periods=3).mean()

    return risa, hawks, roster, merged

# ── Helpers communs ───────────────────────────────────────
def style_ax(ax, ymax=None, ylabel=None, fmt=None):
    ax.set_facecolor(STYLE["bg"])
    ax.tick_params(colors=STYLE["dim"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(STYLE["grid"])
        spine.set_linewidth(0.5)
    ax.grid(axis="y", color=STYLE["grid"],
            linewidth=0.4, alpha=0.5)
    if ymax:
        ax.set_ylim(0, ymax)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9,
                      color=STYLE["muted"], labelpad=6)
    if fmt:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt))

def add_allstar_line(ax, x_pos, ymax):
    ax.axvline(x_pos, color=STYLE["muted"],
               linewidth=1.2, linestyle="--", alpha=0.6)
    ax.text(x_pos + 0.3, ymax * 0.96, "All-Star\nBreak",
            fontsize=7.5, color=STYLE["muted"], va="top")

def add_rolling(ax, x, vals, color, label):
    mask = ~pd.isna(vals)
    ax.plot(x[mask], vals[mask],
            color=color, linewidth=2.2,
            zorder=5, label=label)

def add_header(fig, title, subtitle=None):
    fig.text(0.5, 0.97, title,
             ha="center", va="top",
             fontsize=17, fontweight="bold",
             color=STYLE["text"])
    if subtitle:
        fig.text(0.5, 0.935, subtitle,
                 ha="center", va="top",
                 fontsize=10, color=STYLE["muted"])

def add_footer(fig):
    fig.text(0.5, 0.01, "nba_api · stats.nba.com",
             ha="center", fontsize=7.5,
             color=STYLE["dim"], va="bottom")

def add_legende_points(ax, moy, label_sup, label_inf,
                        x_pos=0.01, y_pos=0.97):
    """Légende points verts / rouges standardisée."""
    handles = [
        mpatches.Patch(color=STYLE["made"],
                       label=f"Au-dessus moy. ({moy:.1f} {label_sup})"),
        mpatches.Patch(color=STYLE["missed"],
                       label=f"En-dessous moy. ({moy:.1f} {label_inf})"),
    ]
    return handles

def savefig(fig, filename):
    os.makedirs("plots", exist_ok=True)
    path = f"plots/{filename}"
    fig.savefig(path, dpi=180, bbox_inches="tight",
                facecolor=STYLE["bg"])
    print(f"Sauvegardé : {path}")

# ══════════════════════════════════════════════════════════
# G1 — Points par match
# ══════════════════════════════════════════════════════════
def graph_points_par_match():
    _, _, _, merged = load_data()

    x      = merged["MATCH_NUM"].values
    N      = len(merged)
    idx_as = merged[merged["GAME_DATE"] <= ALL_STAR_DATE].index[-1]
    moy    = merged["PTS_risa"].mean()

    fig, ax = plt.subplots(figsize=(14, 7), facecolor=STYLE["bg"])
    fig.subplots_adjust(top=0.88, bottom=0.1,
                        left=0.07, right=0.96)

    # Zones avant / après
    ax.axvspan(1, idx_as + 1,
               color=STYLE["neutral"], alpha=0.04)
    ax.axvspan(idx_as + 1, N,
               color=STYLE["accent"], alpha=0.04)

    # Points colorés
    colors = [STYLE["made"] if v >= moy else STYLE["missed"]
              for v in merged["PTS_risa"]]
    ax.scatter(x, merged["PTS_risa"],
               c=colors, s=30, alpha=0.55,
               zorder=4, linewidths=0)

    # Courbe glissante
    add_rolling(ax, x, merged["pts_rolling"],
                STYLE["accent"], "Moy. glissante 10 matchs")

    # Ligne moyenne
    ax.axhline(moy, color=STYLE["dim"],
               linewidth=0.8, linestyle="--", alpha=0.6)
    ax.text(N + 0.5, moy, f"Moy.\n{moy:.1f} pts",
            fontsize=7.5, color=STYLE["dim"], va="center")

    # All-Star
    add_allstar_line(ax, idx_as + 1, 45)

    # Annotations avant / après
    avant = merged[merged["GAME_DATE"] <  ALL_STAR_DATE]
    apres = merged[merged["GAME_DATE"] >= ALL_STAR_DATE]
    moy_av = avant["PTS_risa"].mean()
    moy_ap = apres["PTS_risa"].mean()
    diff   = moy_ap - moy_av
    sign   = "+" if diff >= 0 else ""
    d_col  = STYLE["made"] if diff >= 0 else STYLE["missed"]

    for mid, val, color, label in [
        ((1 + idx_as) / 2, moy_av, STYLE["neutral"],
         f"Avant All-Star\n{moy_av:.1f} pts/match"),
        ((idx_as + N) / 2, moy_ap, STYLE["accent"],
         f"Après All-Star\n{moy_ap:.1f} pts/match"),
    ]:
        ax.text(mid, 3, label, ha="center", fontsize=9,
                color=color, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.4",
                          facecolor=STYLE["surface"],
                          edgecolor=color + "55",
                          linewidth=0.8))

    # Meilleur / pire
    best  = merged.loc[merged["PTS_risa"].idxmax()]
    worst = merged.loc[merged["PTS_risa"].idxmin()]
    for row_data, label, color, offset in [
        (best,  f"Meilleur\n{int(best['PTS_risa'])} pts",
         STYLE["made"],   +6),
        (worst, f"Pire\n{int(worst['PTS_risa'])} pts",
         STYLE["missed"], -6),
    ]:
        ax.annotate(
            label,
            xy=(row_data["MATCH_NUM"], row_data["PTS_risa"]),
            xytext=(row_data["MATCH_NUM"],
                    row_data["PTS_risa"] + offset),
            fontsize=7.5, color=color,
            ha="center", va="center",
            arrowprops=dict(arrowstyle="-",
                            color=color, lw=0.8, alpha=0.6),
            bbox=dict(boxstyle="round,pad=0.3",
                      facecolor=STYLE["surface"],
                      edgecolor=color + "55",
                      linewidth=0.6)
        )

    # Légende
    leg_handles = [
        *add_legende_points(ax, moy, "pts", "pts"),
        plt.Line2D([0], [0], color=STYLE["accent"],
           linewidth=2.2,
           label="Lissage exponentiel (span=10)"),
    ]
    ax.legend(handles=leg_handles, loc="upper left",
              frameon=True, facecolor=STYLE["surface"],
              edgecolor=STYLE["grid"],
              labelcolor=STYLE["muted"], fontsize=8.5)

    style_ax(ax, ymax=45, ylabel="Points",
             fmt=lambda v, _: f"{int(v)} pts")
    ax.set_xlim(0, N + 5)
    ax.set_xlabel("Numéro de match", fontsize=9,
                  color=STYLE["muted"])

    add_header(fig,
               "Risacher — Points par match 2024-25",
               f"75 matchs  ·  Moy. saison : {moy:.1f} pts  ·  "
               f"Avant All-Star : {moy_av:.1f}  →  "
               f"Après : {moy_ap:.1f}  ({sign}{diff:.1f})")
    add_footer(fig)
    savefig(fig, "g1_points_par_match.png")
    plt.show()

# ══════════════════════════════════════════════════════════
# G2 — Part des points de l'équipe
# ══════════════════════════════════════════════════════════
def graph_part_points_equipe():
    _, _, _, merged = load_data()

    x      = merged["MATCH_NUM"].values
    N      = len(merged)
    idx_as = merged[merged["GAME_DATE"] <= ALL_STAR_DATE].index[-1]
    moy    = merged["pct_pts"].mean()

    fig, ax = plt.subplots(figsize=(14, 7), facecolor=STYLE["bg"])
    fig.subplots_adjust(top=0.88, bottom=0.1,
                        left=0.07, right=0.96)

    ax.axvspan(1, idx_as + 1,
               color=STYLE["neutral"], alpha=0.04)
    ax.axvspan(idx_as + 1, N,
               color=STYLE["accent"], alpha=0.04)

    colors = [STYLE["made"] if v >= moy else STYLE["missed"]
              for v in merged["pct_pts"]]
    ax.scatter(x, merged["pct_pts"],
               c=colors, s=30, alpha=0.55,
               zorder=4, linewidths=0)

    add_rolling(ax, x, merged["pct_rolling"],
                STYLE["accent"], "Moy. glissante 10 matchs")

    ax.axhline(moy, color=STYLE["dim"],
               linewidth=0.8, linestyle="--", alpha=0.6)
    ax.text(N + 0.5, moy, f"Moy.\n{moy:.1f}%",
            fontsize=7.5, color=STYLE["dim"], va="center")

    add_allstar_line(ax, idx_as + 1, 50)

    leg_handles = [
        *add_legende_points(ax, moy, "%", "%"),
        plt.Line2D([0], [0], color=STYLE["accent"],
           linewidth=2.2,
           label="Lissage exponentiel (span=10)"),
    ]
    ax.legend(handles=leg_handles, loc="upper left",
              frameon=True, facecolor=STYLE["surface"],
              edgecolor=STYLE["grid"],
              labelcolor=STYLE["muted"], fontsize=8.5)

    style_ax(ax, ymax=50, ylabel="% points équipe",
             fmt=lambda v, _: f"{int(v)}%")
    ax.set_xlim(0, N + 5)
    ax.set_xlabel("Numéro de match", fontsize=9,
                  color=STYLE["muted"])

    add_header(fig,
               "Risacher — Part des points des Hawks",
               f"Moy. saison : {moy:.1f}% des points de l'équipe par match")
    add_footer(fig)
    savefig(fig, "g2_part_points_equipe.png")
    plt.show()

# ══════════════════════════════════════════════════════════
# G3 — FG% Risacher vs Hawks par mois
# ══════════════════════════════════════════════════════════
def graph_fgpct_vs_hawks():
    _, _, _, merged = load_data()

    mensuel_risa  = (merged.groupby("MOIS")["FG_PCT_risa"]
                     .mean() * 100).reset_index()
    mensuel_hawks = (merged.groupby("MOIS")["FG_PCT_hawks"]
                     .mean() * 100).reset_index()
    mensuel_risa["label"] = (mensuel_risa["MOIS"]
                              .astype(str).map(MOIS_NOMS))

    xm = np.arange(len(mensuel_risa))
    w  = 0.35

    fig, ax = plt.subplots(figsize=(12, 7), facecolor=STYLE["bg"])
    fig.subplots_adjust(top=0.88, bottom=0.12,
                        left=0.08, right=0.96)

    bars_r = ax.bar(xm - w/2, mensuel_risa["FG_PCT_risa"],
                    width=w, color=STYLE["accent"],
                    alpha=0.8, label="Risacher", zorder=3)
    bars_h = ax.bar(xm + w/2, mensuel_hawks["FG_PCT_hawks"],
                    width=w, color=STYLE["neutral"],
                    alpha=0.6, label="Hawks (équipe)", zorder=3)

    for bar, val in zip(bars_r, mensuel_risa["FG_PCT_risa"]):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{val:.1f}%", ha="center", fontsize=8,
                color=STYLE["accent"], fontweight="bold")
    for bar, val in zip(bars_h, mensuel_hawks["FG_PCT_hawks"]):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{val:.1f}%", ha="center", fontsize=8,
                color=STYLE["neutral"])

    ax.set_xticks(xm)
    ax.set_xticklabels(mensuel_risa["label"],
                       fontsize=9, color=STYLE["muted"])
    ax.legend(fontsize=9, facecolor=STYLE["surface"],
              edgecolor=STYLE["grid"],
              labelcolor=STYLE["muted"])

    style_ax(ax, ymax=65, ylabel="FG%",
             fmt=lambda v, _: f"{int(v)}%")

    add_header(fig,
               "Risacher vs Hawks — FG% par mois",
               "Comparaison mensuelle de l'efficacité au tir")
    add_footer(fig)
    savefig(fig, "g3_fgpct_vs_hawks.png")
    plt.show()

# ══════════════════════════════════════════════════════════
# G4 — Usage rate
# ══════════════════════════════════════════════════════════
def graph_usage_rate():
    _, _, _, merged = load_data()

    x      = merged["MATCH_NUM"].values
    N      = len(merged)
    idx_as = merged[merged["GAME_DATE"] <= ALL_STAR_DATE].index[-1]
    moy    = merged["usage"].mean()

    fig, ax = plt.subplots(figsize=(14, 7), facecolor=STYLE["bg"])
    fig.subplots_adjust(top=0.88, bottom=0.1,
                        left=0.07, right=0.96)

    ax.axvspan(1, idx_as + 1,
               color=STYLE["neutral"], alpha=0.04)
    ax.axvspan(idx_as + 1, N,
               color=STYLE["accent"], alpha=0.04)

    colors = [STYLE["made"] if v >= moy else STYLE["missed"]
              for v in merged["usage"]]
    ax.scatter(x, merged["usage"],
               c=colors, s=30, alpha=0.55,
               zorder=4, linewidths=0)

    add_rolling(ax, x, merged["usage_rolling"],
                STYLE["accent"], "Moy. glissante 10 matchs")

    ax.axhline(moy, color=STYLE["dim"],
               linewidth=0.8, linestyle="--", alpha=0.6)
    ax.text(N + 0.5, moy, f"Moy.\n{moy:.1f}%",
            fontsize=7.5, color=STYLE["dim"], va="center")

    add_allstar_line(ax, idx_as + 1, 40)

    leg_handles = [
        *add_legende_points(ax, moy, "%", "%"),
        plt.Line2D([0], [0], color=STYLE["accent"],
           linewidth=2.2,
           label="Lissage exponentiel (span=10)"),
    ]
    ax.legend(handles=leg_handles, loc="upper left",
              frameon=True, facecolor=STYLE["surface"],
              edgecolor=STYLE["grid"],
              labelcolor=STYLE["muted"], fontsize=8.5)

    style_ax(ax, ymax=40, ylabel="% tirs de l'équipe",
             fmt=lambda v, _: f"{int(v)}%")
    ax.set_xlim(0, N + 5)
    ax.set_xlabel("Numéro de match", fontsize=9,
                  color=STYLE["muted"])

    add_header(fig,
               "Risacher — Usage rate 2024-25",
               f"Part des tirs Hawks tentés par Risacher · Moy. {moy:.1f}%")
    add_footer(fig)
    savefig(fig, "g4_usage_rate.png")
    plt.show()

# ══════════════════════════════════════════════════════════
# G5 — Classement roster Hawks
# ══════════════════════════════════════════════════════════
def graph_classement_roster():
    _, _, roster, _ = load_data()

    # Top 12 par points, trié croissant pour barh
    top = (roster
           .sort_values("PTS", ascending=True)
           .tail(12)
           .reset_index(drop=True))

    # Noms complets sans coupure
    top["NOM_COURT"] = top["PLAYER_NAME"].apply(
        lambda n: n if len(n) <= 18 else
        f"{n.split()[0][0]}. {' '.join(n.split()[1:])}"
    )

    fig, ax = plt.subplots(figsize=(13, 8), facecolor=STYLE["bg"])
    fig.subplots_adjust(top=0.88, bottom=0.08,
                        left=0.22, right=0.88)

    colors_bar = [
        STYLE["accent"] if "Risacher" in n
        else STYLE["neutral"]
        for n in top["PLAYER_NAME"]
    ]

    bars = ax.barh(
        top["NOM_COURT"], top["PTS"],
        color=colors_bar, alpha=0.8,
        height=0.6, zorder=3
    )

    # Valeur + stats à droite de chaque barre
    for bar, (_, row) in zip(bars, top.iterrows()):
        is_risa = "Risacher" in row["PLAYER_NAME"]
        ax.text(
            bar.get_width() + top["PTS"].max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{int(row['PTS'])} pts  ·  "
            f"{row['FG_PCT']*100:.1f}% FG  ·  "
            f"{int(row['GP'])} matchs",
            ha="left", va="center",
            fontsize=8.5,
            color=STYLE["accent"] if is_risa else STYLE["muted"],
            fontweight="bold" if is_risa else "normal"
        )

    # Légende
    handles = [
        mpatches.Patch(color=STYLE["accent"],
                       label="Zaccharie Risacher"),
        mpatches.Patch(color=STYLE["neutral"],
                       label="Autres joueurs Hawks"),
    ]
    ax.legend(handles=handles, loc="lower right",
              frameon=True, facecolor=STYLE["surface"],
              edgecolor=STYLE["grid"],
              labelcolor=STYLE["muted"], fontsize=8.5)

    ax.set_facecolor(STYLE["bg"])
    ax.tick_params(axis="y", colors=STYLE["text"],
                   labelsize=9.5)
    ax.tick_params(axis="x", colors=STYLE["dim"],
                   labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(STYLE["grid"])
        spine.set_linewidth(0.5)
    ax.grid(axis="x", color=STYLE["grid"],
            linewidth=0.4, alpha=0.5)
    ax.set_xlabel("Points totaux sur la saison",
                  fontsize=9, color=STYLE["muted"])

    # Marge droite pour les labels
    ax.set_xlim(0, top["PTS"].max() * 1.45)

    add_header(fig,
               "Classement scoreurs — Atlanta Hawks 2024-25",
               "Top 12 · Points totaux saison régulière")
    add_footer(fig)
    savefig(fig, "g5_classement_roster.png")
    plt.show()

# ══════════════════════════════════════════════════════════
# LANCEMENT — décommente ce que tu veux afficher
# ══════════════════════════════════════════════════════════

graph_points_par_match()
#graph_part_points_equipe()
#graph_fgpct_vs_hawks()
#graph_usage_rate()
#graph_classement_roster()