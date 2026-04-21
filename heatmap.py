import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
import seaborn as sns # <--- NOUVEAU
import numpy as np
import os

# ── 1. STYLE (inchangé) ──────────────────────────────────
STYLE = {
    "bg":       "#0a0e1a",
    "surface":  "#111827",
    "grid":     "#1f2937",
    "text":     "#f9fafb",
    "muted":    "#9ca3af",
    "dim":      "#4b5563",
    "accent":   "#e8c547",
    "made":     "#4ade80",
    "missed":   "#f87171",
    "before":   "#60a5fa",
    "after":    "#c084fc",
}

# ── 2. APPLY STYLE (inchangé) ────────────────────────────
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

# ── 3. HELPERS (draw_court & setup_court_ax inchangés) ─────
def add_header(fig, title, subtitle=None, y_title=0.97):
    fig.text(0.5, y_title, title, ha="center", va="top",
             fontsize=17, fontweight="bold", color=STYLE["text"])
    if subtitle:
        fig.text(0.5, y_title - 0.045, subtitle, ha="center", va="top",
                 fontsize=11, color=STYLE["muted"])

def add_footer(fig, source="nba_api · stats.nba.com", y=0.01):
    fig.text(0.5, y, source, ha="center", va="bottom", fontsize=8, color=STYLE["dim"])

def draw_court(ax, color="#ffffff", lw=1, alpha=0.18):
    kw = dict(linewidth=lw, color=color, fill=False, alpha=alpha)
    ax.add_patch(Circle((0, 0), radius=7.5, **kw))
    ax.add_patch(Rectangle((-30,-7.5), 60, -1, linewidth=lw, color=color, alpha=alpha))
    ax.add_patch(Rectangle((-80,-47.5), 160, 190, **kw))
    ax.add_patch(Rectangle((-60,-47.5), 120, 190, **kw))
    ax.add_patch(Arc((0,142.5), 120, 120, theta1=0, theta2=180, **kw))
    ax.add_patch(Arc((0,142.5), 120, 120, theta1=180, theta2=0, linestyle="dashed", **kw))
    ax.add_patch(Arc((0,0), 80, 80, theta1=0, theta2=180, **kw))
    ax.add_patch(Rectangle((-220,-47.5), 0, 140, linewidth=lw, color=color, alpha=alpha))
    ax.add_patch(Rectangle(( 220,-47.5), 0, 140, linewidth=lw, color=color, alpha=alpha))
    ax.add_patch(Arc((0,0), 475, 475, theta1=22, theta2=158, **kw))
    ax.add_patch(Arc((0,422.5), 120, 120, theta1=180, theta2=0, **kw))

def setup_court_ax(ax):
    ax.set_xlim(-260, 260)
    ax.set_ylim(-55, 480)
    ax.set_aspect("equal")
    ax.axis("off")

# ── 4. FONCTION PRINCIPALE (MODIFIÉE POUR KDE) ───────────
def heatmap_risacher_organic(df, player_name="Zaccharie Risacher"):
    # 1. Filtrage strict du joueur
    player_df = df[df["PLAYER_NAME"].str.contains("Risacher", case=False)].copy()
    if player_df.empty:
        print("Joueur introuvable.")
        return

    # 2. Préparation de la figure
    fig = plt.figure(figsize=(12, 11), facecolor=STYLE["bg"])
    ax_court = fig.add_axes([0.05, 0.10, 0.9, 0.85]) # Légère rotation de l'axe
    
    setup_court_ax(ax_court)
    
    # On dessine le terrain AVANT pour qu'il soit sous la heatmap
    draw_court(ax_court, color=STYLE["muted"], alpha=0.5, lw=1.5)

    # --- 3. GÉNÉRATION DES "TÂCHES" DE CHALEUR (KDE) ---
    # sns.kdeplot crée ces zones organiques de densité.
    sns.kdeplot(
        data=player_df,
        x="LOC_X",
        y="LOC_Y",
        fill=True,              # Remplit les contours pour faire des taches
        cmap="Reds",            # Dégradé de rouge (clair à sombre)
        alpha=0.8,              # Transparence globale
        levels=20,              # Nombre de "couches" de la tâche
        thresh=0.1,             # Seuil pour ne pas afficher les tirs très isolés
        bw_adjust=0.8,          # Lissage. <1 = plus détaillé, >1 = plus lisse.
        ax=ax_court,
        zorder=2                # Met la heatmap au-dessus des lignes pâles du terrain
    )

    # 4. Header & Footer
    total_shots = len(player_df)
    add_header(
        fig, 
        f"{player_name.upper()}", 
        f"Zone d'Activité au Tir | Saison 2024-25 | {total_shots} tirs tentés",
        y_title=0.98
    )
    add_footer(fig)
    
    os.makedirs("images", exist_ok=True)
    plt.savefig("plots/heatmap.png",
                dpi=180, bbox_inches="tight", facecolor=STYLE["bg"])

    plt.show()

# Pour l'appeler, utilise le dataframe récupéré via nba_api :
df = pd.read_csv("nba_shots_2024_25.csv")
heatmap_risacher_organic(df)