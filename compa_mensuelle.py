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
    "before":  "#60a5fa",
    "after":   "#c084fc",
}

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "text.color":       STYLE["text"],
    "figure.facecolor": STYLE["bg"],
    "axes.facecolor":   STYLE["bg"],
})

ALL_STAR_DATE = pd.Timestamp("2025-02-16")

MOIS_NOMS = {
    "2024-10": "Oct.",
    "2024-11": "Nov.",
    "2024-12": "Déc.",
    "2025-01": "Jan.",
    "2025-02": "Fév.",
    "2025-03": "Mar.",
    "2025-04": "Avr.",
}

# ── Préparation données par mois ──────────────────────────
def prepare_mensuel(df, player_name="Zaccharie Risacher"):
    p = df[df["PLAYER_NAME"] == player_name].copy()
    p["GAME_DATE"] = pd.to_datetime(p["GAME_DATE"], format="%Y%m%d")
    p["MOIS"]      = p["GAME_DATE"].dt.to_period("M")
    p["PERIODE"]   = p["GAME_DATE"].apply(
        lambda d: "après" if d >= ALL_STAR_DATE else "avant"
    )

    # Points
    p["POINTS"] = p.apply(lambda r:
        3 if (r["SHOT_MADE_FLAG"] == 1
              and r["SHOT_TYPE"] == "3PT Field Goal")
        else 2 if (r["SHOT_MADE_FLAG"] == 1
                   and r["SHOT_TYPE"] == "2PT Field Goal")
        else 0, axis=1
    )

    two   = p[p["SHOT_TYPE"] == "2PT Field Goal"]
    three = p[p["SHOT_TYPE"] == "3PT Field Goal"]
    paint = p[p["SHOT_ZONE_BASIC"].isin([
        "Restricted Area", "In The Paint (Non-RA)"
    ])]

    # Agrégation par mois
    def agg_mois(grp):
        total   = len(grp)
        t2      = grp[grp["SHOT_TYPE"] == "2PT Field Goal"]
        t3      = grp[grp["SHOT_TYPE"] == "3PT Field Goal"]
        pa      = grp[grp["SHOT_ZONE_BASIC"].isin([
            "Restricted Area", "In The Paint (Non-RA)"
        ])]
        n_match = grp["GAME_DATE"].nunique()
        return pd.Series({
            "fg_pct":    grp["SHOT_MADE_FLAG"].mean() * 100,
            "pct2":      t2["SHOT_MADE_FLAG"].mean()  * 100
                         if len(t2) > 0 else 0,
            "pct3":      t3["SHOT_MADE_FLAG"].mean()  * 100
                         if len(t3) > 0 else 0,
            "pts_match": grp["POINTS"].sum() / n_match,
            "vol_match": total / n_match,
            "ratio3":    len(t3) / total * 100,
            "pct_paint": len(pa)  / total * 100,
            "periode":   grp["PERIODE"].iloc[0],
            "n_match":   n_match,
        })

    mensuel = (
        p.groupby("MOIS")
        .apply(agg_mois)
        .reset_index()
    )
    mensuel["mois_label"] = mensuel["MOIS"].astype(str).map(MOIS_NOMS)

    return mensuel

# ── Graphique barres groupées ─────────────────────────────
def barres_allstar(df, player_name="Zaccharie Risacher"):
    mensuel = prepare_mensuel(df, player_name)

    # Métriques à afficher (2 lignes × 3 colonnes)
    METRIQUES = [
        {"key": "fg_pct",    "label": "FG%",
         "unit": "%",  "ymax": 65,  "ref": None},
        {"key": "pct2",      "label": "% Réussite 2pts",
         "unit": "%",  "ymax": 75,  "ref": None},
        {"key": "pct3",      "label": "% Réussite 3pts",
         "unit": "%",  "ymax": 55,  "ref": None},
        {"key": "pts_match", "label": "Points / match",
         "unit": " pts", "ymax": 25, "ref": None},
        {"key": "vol_match", "label": "Tirs tentés / match",
         "unit": " tirs", "ymax": 18, "ref": None},
        {"key": "ratio3",    "label": "% tirs à 3pts",
         "unit": "%",  "ymax": 80,  "ref": None},
    ]

    # Calcul refs saison entière
    for m in METRIQUES:
        m["ref"] = mensuel[m["key"]].mean()

    # Séparation avant / après
    avant = mensuel[mensuel["periode"] == "avant"]
    apres = mensuel[mensuel["periode"] == "après"]

    mois_avant = avant["mois_label"].tolist()
    mois_apres = apres["mois_label"].tolist()

    n_avant = len(mois_avant)
    n_apres = len(mois_apres)
    n_total = n_avant + n_apres 

    # ── Figure 2×3 ────────────────────────────────────────
    fig, axes = plt.subplots(
        2, 3,
        figsize=(18, 10),
        facecolor=STYLE["bg"]
    )
    fig.subplots_adjust(
        left=0.05, right=0.97,
        top=0.88,  bottom=0.13,   # ← plus d'espace en bas
        hspace=0.45, wspace=0.3
    )

    BAR_W = 0.35

    for idx, (ax, m) in enumerate(zip(axes.flatten(), METRIQUES)):
        ax.set_facecolor(STYLE["bg"])
        key   = m["key"]
        label = m["label"]
        unit  = m["unit"]
        ymax  = m["ymax"]
        ref   = m["ref"]

        # Positions x
        x_avant = np.arange(n_avant)
        x_apres = np.arange(n_avant, n_total)

        vals_avant = avant[key].values
        vals_apres = apres[key].values

        # ── Barres avant (bleu) ───────────────────────────
        bars_av = ax.bar(
            x_avant, vals_avant,
            width=BAR_W * 1.6,
            color=STYLE["before"],
            alpha=0.75, zorder=3,
            label="Avant All-Star"
        )

        # ── Barres après (violet) ─────────────────────────
        bars_ap = ax.bar(
            x_apres, vals_apres,
            width=BAR_W * 1.6,
            color=STYLE["after"],
            alpha=0.75, zorder=3,
            label="Après All-Star"
        )

        # ── Valeurs sur les barres ────────────────────────
        for bar, val in zip(bars_av, vals_avant):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + ymax * 0.015,
                f"{val:.1f}",
                ha="center", va="bottom",
                fontsize=7.5, color=STYLE["before"],
                fontweight="bold"
            )
        for bar, val in zip(bars_ap, vals_apres):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + ymax * 0.015,
                f"{val:.1f}",
                ha="center", va="bottom",
                fontsize=7.5, color=STYLE["after"],
                fontweight="bold"
            )

        # ── Ligne référence saison ────────────────────────
        ax.axhline(ref, color=STYLE["accent"],
                   linewidth=1, linestyle="--",
                   alpha=0.6, zorder=2)
        ax.text(n_total - 0.5, ref + ymax * 0.015,
        f"Moy. {ref:.1f}",
        fontsize=7, color=STYLE["accent"],
        ha="right", va="bottom", alpha=0.8)

        # ── Axes ──────────────────────────────────────────
        ax.set_xlim(-0.6, n_total - 0.4)
        ax.set_xticks(list(x_avant) + list(x_apres))
        ax.set_xticklabels(
            mois_avant + mois_apres,
            fontsize=8, color=STYLE["muted"]
        )
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f"{int(v)}{unit}")
        )
        ax.tick_params(colors=STYLE["dim"], labelsize=7.5)
        ax.set_title(label, fontsize=10,
                     fontweight="bold", color=STYLE["text"],
                     pad=6)
        ax.grid(axis="y", color=STYLE["grid"],
                linewidth=0.4, alpha=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor(STYLE["grid"])
            spine.set_linewidth(0.5)

    # ── Légende globale ───────────────────────────────────
    handles = [
        mpatches.Patch(color=STYLE["before"], alpha=0.8,
                       label="Avant All-Star break"),
        mpatches.Patch(color=STYLE["after"],  alpha=0.8,
                       label="Après All-Star break"),
        plt.Line2D([0], [0], color=STYLE["accent"],
                   linewidth=1.5, linestyle="--",
                   label="Moyenne saison"),
    ]
    fig.legend(
    handles=handles,
    loc="lower center",
    ncol=4,                   
    frameon=True,
    facecolor=STYLE["surface"],
    edgecolor=STYLE["grid"],
    labelcolor=STYLE["muted"],
    fontsize=8.5,
    bbox_to_anchor=(0.5, 0.01) 
    )

    # ── Header ────────────────────────────────────────────
    fig.text(0.5, 0.97,
             "Zaccharie Risacher — Avant / Après All-Star Break",
             ha="center", va="top",
             fontsize=18, fontweight="bold",
             color=STYLE["text"])
    fig.text(0.5, 0.935,
             "Comparaison mensuelle · 6 métriques · "
             "All-Star Break = 16 février 2025",
             ha="center", va="top",
             fontsize=10, color=STYLE["muted"])
    fig.text(0.5, 0.005,
             "nba_api · stats.nba.com  ·  "
             "* Points calculés sans lancers francs",
             ha="center", fontsize=7.5,
             color=STYLE["dim"], va="bottom")

    os.makedirs("plots", exist_ok=True)
    plt.savefig("plots/risacher_allstar_split.png",
                dpi=180, bbox_inches="tight",
                facecolor=STYLE["bg"])
    print("Sauvegardé : plots/risacher_allstar_split.png")
    plt.show()

# ── Lancement ─────────────────────────────────────────────
df = pd.read_csv("nba_shots_2024_25.csv")
barres_allstar(df)