import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Circle, Rectangle, Arc
import numpy as np
import os

# ── 1. STYLE (doit être défini EN PREMIER) ────────────────
STYLE = {
    "bg":       "#0a0e1a",
    "surface":  "#111827",
    "grid":     "#1f2937",
    "text":     "#f9fafb",
    "muted":    "#9ca3af",
    "dim":      "#4b5563",
    "accent":   "#e8c547",
    "made":     "#4ade80",
    "missed":   "#fb0000",
    "before":   "#60a5fa",
    "after":    "#c084fc",
}

# ── 2. APPLY STYLE (juste après STYLE) ───────────────────
plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "text.color":       STYLE["text"],
    "axes.labelcolor":  STYLE["muted"],
    "xtick.color":      STYLE["dim"],
    "ytick.color":      STYLE["dim"],
    "axes.facecolor":   STYLE["bg"],
    "figure.facecolor": STYLE["bg"],
    "axes.edgecolor":   STYLE["grid"],
    "grid.color":       STYLE["grid"],
    "grid.alpha":       0.4,
    "axes.spines.top":  False,
    "axes.spines.right":False,
})

# ── 3. HELPERS (après STYLE) ──────────────────────────────
def add_header(fig, title, subtitle=None, y_title=0.97):
    fig.text(0.5, y_title, title,
             ha="center", va="top",
             fontsize=17, fontweight="bold", color=STYLE["text"])
    if subtitle:
        fig.text(0.5, y_title - 0.045, subtitle,
                 ha="center", va="top",
                 fontsize=11, color=STYLE["muted"])

def add_footer(fig, source="nba_api · stats.nba.com", y=0.01):
    fig.text(0.5, y, source,
             ha="center", va="bottom",
             fontsize=8, color=STYLE["dim"])

def draw_court(ax, color="#ffffff", lw=1, alpha=0.18):
    kw = dict(linewidth=lw, color=color, fill=False, alpha=alpha)
    ax.add_patch(Circle((0, 0), radius=7.5, **kw))
    ax.add_patch(Rectangle((-30,-7.5), 60, -1,
                            linewidth=lw, color=color, alpha=alpha))
    ax.add_patch(Rectangle((-80,-47.5), 160, 190, **kw))
    ax.add_patch(Rectangle((-60,-47.5), 120, 190, **kw))
    ax.add_patch(Arc((0,142.5), 120, 120, theta1=0,   theta2=180, **kw))
    ax.add_patch(Arc((0,142.5), 120, 120, theta1=180, theta2=0,
                     linestyle="dashed", **kw))
    ax.add_patch(Arc((0,0), 80, 80, theta1=0, theta2=180, **kw))
    ax.add_patch(Rectangle((-220,-47.5), 0, 140,
                            linewidth=lw, color=color, alpha=alpha))
    ax.add_patch(Rectangle(( 220,-47.5), 0, 140,
                            linewidth=lw, color=color, alpha=alpha))
    ax.add_patch(Arc((0,0), 475, 475, theta1=22, theta2=158, **kw))
    ax.add_patch(Arc((0,422.5), 120, 120, theta1=180, theta2=0, **kw))

def setup_court_ax(ax):
    ax.set_xlim(-260, 260)
    ax.set_ylim(-55, 480)
    ax.set_aspect("equal")
    ax.axis("off")

# ── 4. FONCTION PRINCIPALE ────────────────────────────────
def shot_chart_risacher(df, player_name="Zaccharie Risacher"):
    player_df = df[df["PLAYER_NAME"] == player_name].copy()
    if player_df.empty:
        print(f"Joueur introuvable : {player_name}")
        # Affiche les noms disponibles pour aider
        matches = df[df["PLAYER_NAME"].str.contains(
            "risacher", case=False, na=False
        )]["PLAYER_NAME"].unique()
        print(f"Noms trouvés : {matches}")
        return

    made   = player_df[player_df["SHOT_MADE_FLAG"] == 1]
    missed = player_df[player_df["SHOT_MADE_FLAG"] == 0]

    total  = len(player_df)
    n_made = len(made)
    fg_pct = round(n_made / total * 100, 1)

    two   = player_df[player_df["SHOT_TYPE"] == "2PT Field Goal"]
    three = player_df[player_df["SHOT_TYPE"] == "3PT Field Goal"]
    pct2  = round(two["SHOT_MADE_FLAG"].mean()   * 100, 1) if len(two)   > 0 else 0
    pct3  = round(three["SHOT_MADE_FLAG"].mean() * 100, 1) if len(three) > 0 else 0

    fig = plt.figure(figsize=(12, 10), facecolor=STYLE["bg"])
    ax_court = fig.add_axes([0.02, 0.06, 0.62, 0.86])
    ax_stats = fig.add_axes([0.66, 0.06, 0.32, 0.86])
    ax_court.set_facecolor(STYLE["bg"])
    ax_stats.set_facecolor(STYLE["bg"])
    ax_stats.axis("off")

    draw_court(ax_court)

    ax_court.scatter(missed["LOC_X"], missed["LOC_Y"],
                     c=STYLE["missed"], s=16, alpha=1,
                     marker="x", linewidths=0.9, zorder=3)
    ax_court.scatter(made["LOC_X"], made["LOC_Y"],
                     c=STYLE["accent"], s=22, alpha=1,
                     linewidths=0, zorder=4)

    if "SHOT_ZONE_BASIC" in player_df.columns:
        zone_colors = {
            "Restricted Area":       STYLE["made"],
            "In The Paint (Non-RA)": STYLE["made"], 
            "Mid-Range":             STYLE["muted"],
            "Left Corner 3":         STYLE["accent"],
            "Right Corner 3":        STYLE["accent"],
            "Above the Break 3":     STYLE["accent"],
            "Backcourt":             STYLE["dim"],
        }
        

    setup_court_ax(ax_court)

    s  = ax_stats
    y  = 0.97

    def stat_block(label, value, color, note=None):
        nonlocal y
        y -= 0.08
        s.text(0.08, y, label, transform=s.transAxes,
               color=STYLE["muted"], fontsize=8.5, va="top", family="monospace")
        s.text(0.08, y - 0.055, value, transform=s.transAxes,
               color=color, fontsize=22, fontweight="bold", va="top")
        if note:
            s.text(0.08, y - 0.115, note, transform=s.transAxes,
                   color=STYLE["dim"], fontsize=8, va="top")
        y -= 0.14

    def bar_stat(label, pct, n, made_n, color):
        nonlocal y
        y -= 0.035
        s.text(0.08, y, label, transform=s.transAxes,
               color=STYLE["muted"], fontsize=8.5, va="top", family="monospace")
        s.text(0.92, y, f"{pct}%", transform=s.transAxes,
               color=color, fontsize=13, fontweight="bold", va="top", ha="right")
        s.text(0.08, y - 0.03, f"{n} tentés · {made_n} réussis",
               transform=s.transAxes, color=STYLE["dim"], fontsize=7.5, va="top")
        s.add_patch(Rectangle((0.08, y-0.075), 0.84, 0.014,
                               transform=s.transAxes,
                               color=STYLE["grid"], clip_on=False))
        s.add_patch(Rectangle((0.08, y-0.075), 0.84*(pct/100), 0.014,
                               transform=s.transAxes,
                               color=color, alpha=0.75, clip_on=False))
        y -= 0.135

    s.text(0.5, y, player_name.split()[0],
           transform=s.transAxes, ha="center",
           fontsize=15, fontweight="bold", color=STYLE["accent"], va="top")
    s.text(0.5, y - 0.055, player_name.split()[1],
           transform=s.transAxes, ha="center",
           fontsize=15, fontweight="bold", color=STYLE["text"], va="top")
    y -= 0.13
    s.text(0.5, y, "Atlanta Hawks · Rookie 2024-25",
           transform=s.transAxes, ha="center",
           fontsize=9, color=STYLE["muted"], va="top")
    y -= 0.055
    s.plot([0.05, 0.95], [y, y],
       color=STYLE["grid"], linewidth=0.8,
       transform=s.transAxes, clip_on=False)

    stat_block("FG%", f"{fg_pct}%", STYLE["accent"],
               f"{n_made} réussis sur {total} tentés")
    stat_block("TIRS TENTÉS", str(total), STYLE["text"])

    y -= 0.02
    s.plot([0.05, 0.95], [y, y],
       color=STYLE["grid"], linewidth=0.8,
       transform=s.transAxes, clip_on=False)

    bar_stat("2PT FIELD GOAL", pct2,
             len(two), int(two["SHOT_MADE_FLAG"].sum()), STYLE["accent"])
    bar_stat("3PT FIELD GOAL", pct3,
             len(three), int(three["SHOT_MADE_FLAG"].sum()), STYLE["accent"])

    y -= 0.04
    s.plot([0.05, 0.95], [y, y],
       color=STYLE["grid"], linewidth=0.8,
       transform=s.transAxes, clip_on=False)
    y -= 0.06
    s.text(0.08, y, "LÉGENDE", transform=s.transAxes,
           color=STYLE["dim"], fontsize=8, family="monospace", va="top")
    y -= 0.055
    s.scatter([0.12], [y-0.01], s=55, color=STYLE["accent"], alpha=0.85,
              transform=s.transAxes, zorder=5, clip_on=False)
    s.text(0.19, y-0.01, "Tir réussi", transform=s.transAxes,
           color=STYLE["text"], fontsize=9, va="center")
    y -= 0.06
    s.scatter([0.12], [y-0.01], s=45, color=STYLE["missed"], alpha=0.5,
              marker="x", linewidths=1.5,
              transform=s.transAxes, zorder=5, clip_on=False)
    s.text(0.19, y-0.01, "Tir raté", transform=s.transAxes,
           color=STYLE["text"], fontsize=9, va="center")
    y -= 0.065
    s.text(0.08, y, "Les % indiquent le FG% par zone",
           transform=s.transAxes, color=STYLE["dim"],
           fontsize=7.5, va="top", style="italic")

    add_header(fig, "Shot Chart — Saison régulière 2024-25")
    add_footer(fig)

    os.makedirs("images", exist_ok=True)
    plt.savefig("plots/risacher_shotchart.png",
                dpi=180, bbox_inches="tight", facecolor=STYLE["bg"])
    print("Sauvegardé : plots/risacher_shotchart.png")
    plt.show()

# ── 5. LANCEMENT (toujours en dernier) ────────────────────
df = pd.read_csv("nba_shots_2024_25.csv")
df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])

shot_chart_risacher(df)