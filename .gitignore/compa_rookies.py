import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, Rectangle, Arc
from matplotlib.widgets import Button
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
    "missed":  "#ff0000",
    "neutral": "#60a5fa",
}

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "text.color":       STYLE["text"],
    "figure.facecolor": STYLE["bg"],
    "axes.facecolor":   STYLE["bg"],
})

RISACHER = "Zaccharie Risacher"

ROOKIES = [
    "Alex Sarr",
    "Reed Sheppard",
    "Stephon Castle",
    "Ronald Holland II",
    "Tidjane Salaün",
    "Donovan Clingan",
    "Rob Dillingham",
    "Zach Edey",
    "Cody Williams",
]

METRIQUES = [
    {"key": "fg_pct",    "label": "FG%",           "unit": "%",    "fmt": ".1f", "max": 70},
    {"key": "pct3",      "label": "3P%",            "unit": "%",    "fmt": ".1f", "max": 60},
    {"key": "pct2",      "label": "2P%",            "unit": "%",    "fmt": ".1f", "max": 80},
    {"key": "ratio3",    "label": "% tirs pris à 3pts",  "unit": "%",    "fmt": ".1f", "max": 100},
    {"key": "pct_paint", "label": "% Peinture",        "unit": "%",    "fmt": ".1f", "max": 100},
    {"key": "dist",      "label": "Dist. moy.",     "unit": " ft",  "fmt": ".1f", "max": 25},
]

# ── Calcul métriques ──────────────────────────────────────
def compute_metrics(df, name):
    p     = df[df["PLAYER_NAME"] == name]
    total = len(p)
    if total == 0:
        return None
    two   = p[p["SHOT_TYPE"] == "2PT Field Goal"]
    three = p[p["SHOT_TYPE"] == "3PT Field Goal"]
    paint = p[p["SHOT_ZONE_BASIC"].isin([
        "Restricted Area", "In The Paint (Non-RA)"
    ])]
    return {
        "name":      name,
        "fg_pct":    p["SHOT_MADE_FLAG"].mean() * 100,
        "pct3":      three["SHOT_MADE_FLAG"].mean() * 100 if len(three) > 0 else 0,
        "pct2":      two["SHOT_MADE_FLAG"].mean()   * 100 if len(two)   > 0 else 0,
        "ratio3":    len(three) / total * 100,
        "pct_paint": len(paint)  / total * 100,
        "dist":      p["SHOT_DISTANCE"].mean(),
        "volume":    total,
    }

# ── Terrain ───────────────────────────────────────────────
def draw_court(ax, color="#ffffff", lw=0.8, alpha=0.18):
    kw = dict(linewidth=lw, color=color, fill=False, alpha=alpha)
    ax.add_patch(Circle((0, 0), radius=7.5, **kw))
    ax.add_patch(Rectangle((-30,-7.5), 60, -1,
                            linewidth=lw, color=color, alpha=alpha))
    ax.add_patch(Rectangle((-80,-47.5), 160, 190, **kw))
    ax.add_patch(Rectangle((-60,-47.5), 120, 190, **kw))
    ax.add_patch(Arc((0,142.5), 120, 120,
                     theta1=0, theta2=180, **kw))
    ax.add_patch(Arc((0,142.5), 120, 120,
                     theta1=180, theta2=0, linestyle="dashed", **kw))
    ax.add_patch(Arc((0,0), 80, 80,
                     theta1=0, theta2=180, **kw))
    ax.add_patch(Rectangle((-220,-47.5), 0, 140,
                            linewidth=lw, color=color, alpha=alpha))
    ax.add_patch(Rectangle(( 220,-47.5), 0, 140,
                            linewidth=lw, color=color, alpha=alpha))
    ax.add_patch(Arc((0,0), 475, 475,
                     theta1=22, theta2=158, **kw))
    ax.add_patch(Arc((0,422.5), 120, 120,
                     theta1=180, theta2=0, **kw))

def setup_court_ax(ax):
    ax.set_xlim(-260, 260)
    ax.set_ylim(-55, 420)
    ax.set_aspect("equal")
    ax.axis("off")

# ── Dessin shot chart ─────────────────────────────────────
def draw_shotchart(ax, player_df, color_made, size=8, alpha=0.7):
    made   = player_df[player_df["SHOT_MADE_FLAG"] == 1]
    missed = player_df[player_df["SHOT_MADE_FLAG"] == 0]
    draw_court(ax)
    ax.scatter(missed["LOC_X"], missed["LOC_Y"],
               c=STYLE["missed"], s=size * 0.6,
               alpha=1, marker="x",
               linewidths=0.7, zorder=3)
    ax.scatter(made["LOC_X"], made["LOC_Y"],
               c=color_made, s=size,
               alpha=1, linewidths=0, zorder=4)
    setup_court_ax(ax)

# ── Dessin bar chart comparatif ───────────────────────────
def draw_bars(ax, m_risa, m_other, other_name):
    ax.set_facecolor(STYLE["bg"])
    ax.axis("off")

    N   = len(METRIQUES)
    y   = 0.92
    DY  = 0.82 / N

    ax.text(0.5, 0.98, "Comparaison statistiques",
            transform=ax.transAxes, ha="center",
            fontsize=10, fontweight="bold",
            color=STYLE["text"], va="top")

    for m in METRIQUES:
        key   = m["key"]
        label = m["label"]
        unit  = m["unit"]
        fmt   = m["fmt"]
        vmax  = m["max"]

        v_risa  = m_risa[key]
        v_other = m_other[key]

        # Valeur textuelle
        if fmt == "d":
            s_risa  = f"{int(v_risa)}{unit}"
            s_other = f"{int(v_other)}{unit}"
        else:
            s_risa  = f"{v_risa:{fmt}}{unit}"
            s_other = f"{v_other:{fmt}}{unit}"

        y -= DY

        # Label métrique centré
        ax.text(0.5, y + 0.06, label,
                transform=ax.transAxes, ha="center",
                fontsize=8, color=STYLE["muted"],
                fontweight="600", va="top",
                family="monospace")

        BAR_H  = 0.028
        BAR_Y  = y 
        BAR_W  = 0.38   # largeur max d'une barre

        # ── Risacher (gauche, doré) ────────────────────
        norm_risa  = min(v_risa  / vmax, 1.0)
        norm_other = min(v_other / vmax, 1.0)

        winner_risa  = v_risa  >= v_other
        winner_other = v_other >  v_risa

        # Fond barre Risacher
        ax.add_patch(plt.Rectangle(
            (0.5 - BAR_W, BAR_Y), BAR_W, BAR_H,
            transform=ax.transAxes,
            facecolor=STYLE["surface"], edgecolor="none",
            clip_on=False
        ))
        # Barre Risacher (partant de droite vers gauche)
        ax.add_patch(plt.Rectangle(
            (0.5 - BAR_W * norm_risa, BAR_Y),
            BAR_W * norm_risa, BAR_H,
            transform=ax.transAxes,
            facecolor=STYLE["accent"],
            alpha=0.9 if winner_risa else 0.45,
            edgecolor="none", clip_on=False
        ))

        # Fond barre adversaire
        ax.add_patch(plt.Rectangle(
            (0.5, BAR_Y), BAR_W, BAR_H,
            transform=ax.transAxes,
            facecolor=STYLE["surface"], edgecolor="none",
            clip_on=False
        ))
        # Barre adversaire (partant de gauche vers droite)
        ax.add_patch(plt.Rectangle(
            (0.5, BAR_Y),
            BAR_W * norm_other, BAR_H,
            transform=ax.transAxes,
            facecolor=STYLE["neutral"],
            alpha=0.9 if winner_other else 0.45,
            edgecolor="none", clip_on=False
        ))

        # Ligne centrale
        ax.plot([0.5, 0.5],
                [BAR_Y - 0.005, BAR_Y + BAR_H + 0.005],
                transform=ax.transAxes,
                color=STYLE["grid"], linewidth=1.2,
                clip_on=False)

        # Valeurs textuelles
        ax.text(0.5 - BAR_W * norm_risa - 0.01,
                BAR_Y + BAR_H / 2,
                s_risa,
                transform=ax.transAxes,
                ha="right", va="center",
                fontsize=8.5, fontweight="bold",
                color=STYLE["accent"] if winner_risa else STYLE["dim"])

        ax.text(0.5 + BAR_W * norm_other + 0.01,
                BAR_Y + BAR_H / 2,
                s_other,
                transform=ax.transAxes,
                ha="left", va="center",
                fontsize=8.5, fontweight="bold",
                color=STYLE["neutral"] if winner_other else STYLE["dim"])

        # Indicateur victoire
        if winner_risa:
            ax.text(0.5 - 0.015, BAR_Y + BAR_H / 2, "◀",
                    transform=ax.transAxes, ha="right",
                    va="center", fontsize=7,
                    color=STYLE["accent"], alpha=0.8)
        else:
            ax.text(0.5 + 0.015, BAR_Y + BAR_H / 2, "▶",
                    transform=ax.transAxes, ha="left",
                    va="center", fontsize=7,
                    color=STYLE["neutral"], alpha=0.8)

    # Score global (nb de métriques gagnées)
    wins_risa  = sum(
        1 for m in METRIQUES if m_risa[m["key"]] >= m_other[m["key"]]
    )
    wins_other = N - wins_risa

    ax.text(0.5, 0.03,
            f"{wins_risa}  –  {wins_other}",
            transform=ax.transAxes, ha="center",
            fontsize=16, fontweight="bold",
            color=STYLE["text"], va="bottom")
    ax.text(0.5, 0.0,
            "métriques remportées",
            transform=ax.transAxes, ha="center",
            fontsize=7.5, color=STYLE["dim"], va="bottom")

# ── Figure principale ─────────────────────────────────────
class ComparaisonApp:
    def __init__(self, df):
        self.df          = df
        self.current_idx = 0
        self.m_risa      = compute_metrics(df, RISACHER)
        self.df_risa     = df[df["PLAYER_NAME"] == RISACHER]

        # ── Layout ────────────────────────────────────────
        # [shot Risacher | bars | shot adversaire | boutons]
        self.fig = plt.figure(figsize=(18, 10),
                              facecolor=STYLE["bg"])
        self.fig.subplots_adjust(
            left=0.01, right=0.99,
            top=0.88,  bottom=0.14
        )

        gs = self.fig.add_gridspec(
            1, 3,
            width_ratios=[2, 1.6, 2],
            wspace=0.08
        )

        self.ax_risa  = self.fig.add_subplot(gs[0])
        self.ax_bars  = self.fig.add_subplot(gs[1])
        self.ax_other = self.fig.add_subplot(gs[2])

        for ax in [self.ax_risa, self.ax_bars, self.ax_other]:
            ax.set_facecolor(STYLE["bg"])

        # Titre Risacher fixe
        self.fig.text(
            0.18, 0.93,
            "Zaccharie Risacher",
            ha="center", fontsize=14,
            fontweight="bold", color=STYLE["accent"]
        )
        self.fig.text(
            0.18, 0.895,
            "Hawks · Pick #1",
            ha="center", fontsize=9,
            color=STYLE["muted"]
        )

        # Titre global
        self.fig.text(
            0.5, 0.97,
            "Comparaison — Rookies 2024-25",
            ha="center", fontsize=18,
            fontweight="bold", color=STYLE["text"]
        )

        # Footer
        self.fig.text(
            0.5, 0.01,
            "nba_api · stats.nba.com",
            ha="center", fontsize=7.5,
            color=STYLE["dim"], va="bottom"
        )

        # ── Boutons sélection rookie ───────────────────────
        N       = len(ROOKIES)
        BTN_W   = 0.062
        BTN_H   = 0.038
        BTN_GAP = 0.004
        START_X = 0.01
        BTN_Y   = 0.03

        self.buttons = []
        self.btn_axes = []

        for i, name in enumerate(ROOKIES):
            row  = i // 10
            col  = i  % 10
            bx   = START_X + col * (BTN_W + BTN_GAP)
            by   = BTN_Y   + row * (BTN_H + BTN_GAP)
            bax  = self.fig.add_axes([bx, by, BTN_W, BTN_H])
            bax.set_facecolor(STYLE["surface"])

            short = name.split()[1]   # nom de famille
            btn   = Button(
                bax, short,
                color=STYLE["surface"],
                hovercolor=STYLE["grid"]
            )
            btn.label.set_fontsize(7.5)
            btn.label.set_color(STYLE["muted"])
            btn.on_clicked(lambda _, idx=i: self.select(idx))
            self.buttons.append(btn)
            self.btn_axes.append(bax)

        # Rendu initial
        self.render(0)

    def select(self, idx):
        self.current_idx = idx
        # Reset couleurs boutons
        for i, (btn, bax) in enumerate(
            zip(self.buttons, self.btn_axes)
        ):
            if i == idx:
                bax.set_facecolor(STYLE["neutral"] + "44")
                btn.label.set_color(STYLE["neutral"])
            else:
                bax.set_facecolor(STYLE["surface"])
                btn.label.set_color(STYLE["muted"])
        self.render(idx)
        self.fig.canvas.draw_idle()

    def render(self, idx):
        other_name = ROOKIES[idx]
        df_other   = self.df[self.df["PLAYER_NAME"] == other_name]
        m_other    = compute_metrics(self.df, other_name)

        # Nettoyage axes
        self.ax_risa.cla()
        self.ax_bars.cla()
        self.ax_other.cla()

        for ax in [self.ax_risa, self.ax_bars, self.ax_other]:
            ax.set_facecolor(STYLE["bg"])

        # ── Shot chart Risacher ────────────────────────────
        draw_shotchart(
            self.ax_risa, self.df_risa,
            color_made=STYLE["accent"],
            size=10, alpha=0.75
        )
        # Stats Risacher sous le terrain
        fg  = self.m_risa["fg_pct"]
        p3  = self.m_risa["pct3"]
        vol = self.m_risa["volume"]
        self.ax_risa.text(
            0, -45,
            f"{fg:.1f}% FG  ·  {p3:.1f}% 3P  ·  {vol} tirs",
            ha="center", fontsize=8.5,
            color=STYLE["accent"], fontweight="bold",
            transform=self.ax_risa.transData
        )

        # ── Bar chart ─────────────────────────────────────
        draw_bars(self.ax_bars, self.m_risa, m_other, other_name)

        # ── Shot chart adversaire ──────────────────────────
        draw_shotchart(
            self.ax_other, df_other,
            color_made=STYLE["neutral"],
            size=8, alpha=0.65
        )
        fg2  = m_other["fg_pct"]
        p3b  = m_other["pct3"]
        vol2 = m_other["volume"]
        self.ax_other.text(
            0, -45,
            f"{fg2:.1f}% FG  ·  {p3b:.1f}% 3P  ·  {vol2} tirs",
            ha="center", fontsize=8.5,
            color=STYLE["neutral"], fontweight="bold",
            transform=self.ax_other.transData
        )

        # Titre adversaire (mis à jour dynamiquement)
        parts = other_name.split()
        self.fig.texts = [
            t for t in self.fig.texts
            if t.get_text() not in [
                t2.get_text()
                for t2 in self.fig.texts
                if t2.get_position()[0] > 0.65
                and t2.get_position()[1] > 0.87
            ]
        ]

        # Supprime anciens titres adversaire et réécrit
        for txt in list(self.fig.texts):
            x, y = txt.get_position()
            if x > 0.65 and y > 0.87:
                txt.remove()

        self.fig.text(
            0.82, 0.93,
            other_name,
            ha="center", fontsize=14,
            fontweight="bold", color=STYLE["neutral"]
        )
        self.fig.text(
            0.82, 0.895,
            f"Pick #{idx + 2}",
            ha="center", fontsize=9,
            color=STYLE["muted"]
        )

        # Active le bouton sélectionné
        self.btn_axes[idx].set_facecolor(STYLE["neutral"] + "44")
        self.buttons[idx].label.set_color(STYLE["neutral"])

def save_comparison(df, rookie_name, idx):
    """Génère et sauvegarde le PNG de comparaison Risacher vs un rookie."""
    m_risa  = compute_metrics(df, RISACHER)
    m_other = compute_metrics(df, rookie_name)
    df_risa = df[df["PLAYER_NAME"] == RISACHER]
    df_other= df[df["PLAYER_NAME"] == rookie_name]

    if not m_risa or not m_other:
        print(f"  Données manquantes : {rookie_name}")
        return

    fig = plt.figure(figsize=(18, 10), facecolor=STYLE["bg"])
    fig.subplots_adjust(left=0.01, right=0.99,
                        top=0.88, bottom=0.06)

    gs = fig.add_gridspec(1, 3,
                          width_ratios=[2, 1.6, 2],
                          wspace=0.08)
    ax_risa  = fig.add_subplot(gs[0])
    ax_bars  = fig.add_subplot(gs[1])
    ax_other = fig.add_subplot(gs[2])

    for ax in [ax_risa, ax_bars, ax_other]:
        ax.set_facecolor(STYLE["bg"])

    # Shot chart Risacher
    draw_shotchart(ax_risa, df_risa,
                   color_made=STYLE["accent"],
                   size=10, alpha=0.75)
    fg  = m_risa["fg_pct"]
    p3  = m_risa["pct3"]
    vol = m_risa["volume"]
    ax_risa.text(0, -45,
                 f"{fg:.1f}% FG  ·  {p3:.1f}% 3P  ·  {vol} tirs",
                 ha="center", fontsize=8.5,
                 color=STYLE["accent"], fontweight="bold",
                 transform=ax_risa.transData)

    # Bars
    draw_bars(ax_bars, m_risa, m_other, rookie_name)

    # Shot chart adversaire
    draw_shotchart(ax_other, df_other,
                   color_made=STYLE["neutral"],
                   size=8, alpha=0.65)
    fg2  = m_other["fg_pct"]
    p3b  = m_other["pct3"]
    vol2 = m_other["volume"]
    ax_other.text(0, -45,
                  f"{fg2:.1f}% FG  ·  {p3b:.1f}% 3P  ·  {vol2} tirs",
                  ha="center", fontsize=8.5,
                  color=STYLE["neutral"], fontweight="bold",
                  transform=ax_other.transData)

    # Titres
    fig.text(0.5, 0.97,
             "Comparaison — Rookies 2024-25",
             ha="center", fontsize=18,
             fontweight="bold", color=STYLE["text"])
    fig.text(0.18, 0.93, "Zaccharie Risacher",
             ha="center", fontsize=14,
             fontweight="bold", color=STYLE["accent"])
    fig.text(0.18, 0.895, "Hawks · Pick #1",
             ha="center", fontsize=9,
             color=STYLE["muted"])
    fig.text(0.82, 0.93, rookie_name,
             ha="center", fontsize=14,
             fontweight="bold", color=STYLE["neutral"])
    fig.text(0.82, 0.895, f"Pick #{idx + 2}",
             ha="center", fontsize=9,
             color=STYLE["muted"])
    fig.text(0.5, 0.01, "nba_api · stats.nba.com",
             ha="center", fontsize=7.5,
             color=STYLE["dim"], va="bottom")

    # Slug pour le nom de fichier
    slug = (rookie_name.lower()
            .replace(" ", "_")
            .replace("ü", "u")
            .replace("'", "")
            .replace("é", "e"))
    path = f"plots/comparaison_{slug}.png"
    fig.savefig(path, dpi=130,
                bbox_inches="tight",
                facecolor=STYLE["bg"])
    plt.close(fig)
    print(f"  OK : {path}")


def generate_all_comparisons():
    print("Chargement des données...")
    df = pd.read_csv("nba_shots_2024_25.csv")

    os.makedirs("plots", exist_ok=True)
    print("Génération des comparaisons...")
    for i, name in enumerate(ROOKIES):
        print(f"  [{i+1}/{len(ROOKIES)}] {name}...")
        save_comparison(df, name, i)

    print(f"\nTerminé — {len(ROOKIES)} PNG générés dans plots/")


# ── Lancement ─────────────────────────────────────────────
generate_all_comparisons()

# ── Lancement ─────────────────────────────────────────────
df  = pd.read_csv("nba_shots_2024_25.csv")
app = ComparaisonApp(df)
plt.show()