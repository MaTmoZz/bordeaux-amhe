import streamlit as st
import pandas as pd
from pathlib import Path
import numpy as np
import random
from collections import Counter

ALPHA = 0.5  # poids du rang
BETA = 0.5   # poids du ratio
K = 8        # intensité de la différence de niveau

# -------------------------
# Configuration de la page
# -------------------------
st.set_page_config(
    page_title="Burdigala Fédéral – Épée Longue",
    layout="wide"
)

st.title("⚔️ Burdigala Fédéral – Épée Longue (AMHE)")
st.caption("Analyse des combattants inscrits")

# -------------------------
# Chargement automatique du fichier Excel
# -------------------------
DATA_FILE = Path("combattants_burdigala.xlsx")

if not DATA_FILE.exists():
    st.error("❌ Fichier Excel introuvable : combattants_burdigala.xlsx")
    st.stop()

df = pd.read_excel(DATA_FILE)

# Nettoyage du rang (gestion des "?")
df["Rang"] = pd.to_numeric(df["Rang"], errors="coerce")

# -------------------------
# Informations générales
# -------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Nombre de combattants", len(df))
col2.metric("Nombre de clubs", df["Club"].nunique())
col3.metric("Nationalités représentées", df["Nationalité"].nunique())

st.divider()

# -------------------------
# Favoris du tournoi
# -------------------------
st.header("🔥 Favoris du tournoi")

top_n = st.slider(
    "Nombre de favoris à afficher",
    min_value=3,
    max_value=20,
    value=8
)

favoris = (
    df.dropna(subset=["Rang"])
      .sort_values("Rang")
      .head(top_n)
)

st.dataframe(
    favoris[["Combattant", "Club", "Nationalité", "Rang"]],
    use_container_width=True,
    hide_index=True
)

# -------------------------
# Clubs représentés
# -------------------------
st.header("🏛️ Clubs représentés")

clubs = (
    df.groupby("Club")
      .size()
      .reset_index(name="Nombre de combattants")
      .sort_values("Nombre de combattants", ascending=False)
)

st.dataframe(
    clubs,
    use_container_width=True,
    hide_index=True
)


# -------------------------
# Statistiques complémentaires
# -------------------------
st.header("📊 Statistiques complémentaires")

col4, col5 = st.columns(2)

with col4:
    st.subheader("Rang mondial")
    if df["Rang"].notna().any():
        st.write(f"Rang moyen : **{int(df['Rang'].mean())}**")
        st.write(f"Meilleur rang : **{int(df['Rang'].min())}**")
        st.write(f"Rang médian : **{int(df['Rang'].median())}**")
    else:
        st.write("Aucun rang connu")

with col5:
    st.subheader("Rangs inconnus")
    inconnus = df["Rang"].isna().sum()
    st.metric("Combattants sans rang", inconnus)

# -------------------------
# Tableau complet
# -------------------------
st.header("📋 Liste complète des combattants")

st.dataframe(
    df.sort_values("Rang", na_position="last"),
    use_container_width=True,
    hide_index=True
)


# -------------------------
# Calcul du ratio de performance (HEMA Ratings)
# -------------------------

# Paramètres du modèle
DRAW_WEIGHT = 0.5   # une égalité = demi-victoire
SMOOTHING_C = 2     # lissage pour carrières courtes


def performance_ratio(wins, losses, draws, c=SMOOTHING_C, draw_weight=DRAW_WEIGHT):
    """
    Calcule un ratio de performance robuste à partir
    des victoires, défaites et égalités.
    """
    # Sécurité : valeurs manquantes
    if pd.isna(wins) or pd.isna(losses) or pd.isna(draws):
        return None

    wins = int(wins)
    losses = int(losses)
    draws = int(draws)

    total = wins + losses + draws

    # Aucun combat enregistré
    if total == 0:
        return 0.5  # neutre

    return (wins + draw_weight * draws + c) / (total + 2 * c)


# Calcul du nombre total de combats
df["Nb_combats"] = df["Wins"] + df["Losses"] + df["Draws"]

# Calcul du ratio
df["Ratio"] = df.apply(
    lambda row: performance_ratio(
        row["Wins"],
        row["Losses"],
        row["Draws"]
    ),
    axis=1
)

# Indicateur de fiabilité du ratio (optionnel mais recommandé)
df["Fiabilite_ratio"] = df["Nb_combats"] / (df["Nb_combats"] + 10)


st.header("📈 Ratios de performance (HEMA Ratings)")

st.dataframe(
    df[
        [
            "Combattant",
            "Wins",
            "Losses",
            "Draws",
            "Nb_combats",
            "Ratio",
            "Fiabilite_ratio"
        ]
    ].sort_values("Ratio", ascending=False),
    use_container_width=True,
    hide_index=True
)


# -------------------------
# Ratio effectif pondéré par la fiabilité
# -------------------------

df["Ratio_effectif"] = (
    0.5 + df["Fiabilite_ratio"] * (df["Ratio"] - 0.5)
)


# -------------------------
# Calcul de probabilité de victoire
# -------------------------


def puissance_combattant(row, alpha=ALPHA, beta=BETA):
    score = 0

    # Rang mondial
    if not pd.isna(row["Rang"]) and row["Rang"] > 0:
        score += alpha * (1 / row["Rang"])

    # Ratio pondéré par la fiabilité
    score += beta * row["Ratio_effectif"]

    return score


def proba_victoire(score_a, score_b, k=K):
    """
    Probabilité que A batte B (logistique).
    """
    return 1 / (1 + np.exp(-k * (score_a - score_b)))



st.divider()
st.header("⚔️ Duel entre deux combattants")

combattants = sorted(df["Combattant"].unique())

col1, col2 = st.columns(2)

with col1:
    combattant_a = st.selectbox(
        "Combattant A",
        combattants,
        key="combat_a"
    )

with col2:
    combattant_b = st.selectbox(
        "Combattant B",
        combattants,
        key="combat_b"
    )

if combattant_a == combattant_b:
    st.warning("Veuillez sélectionner deux combattants différents.")
else:
    row_a = df[df["Combattant"] == combattant_a].iloc[0]
    row_b = df[df["Combattant"] == combattant_b].iloc[0]

    score_a = puissance_combattant(row_a)
    score_b = puissance_combattant(row_b)

    proba_a = proba_victoire(score_a, score_b)
    proba_b = 1 - proba_a

    st.subheader("📊 Résultat du duel")

    col3, col4 = st.columns(2)

    with col3:
        st.metric(
            label=f"Victoire {combattant_a}",
            value=f"{proba_a * 100:.1f} %"
        )

    with col4:
        st.metric(
            label=f"Victoire {combattant_b}",
            value=f"{proba_b * 100:.1f} %"
        )

    # Détails (optionnel mais très utile)
    with st.expander("🔍 Détails du calcul"):
        st.write(f"**Score {combattant_a}** : {score_a:.4f}")
        st.write(f"**Score {combattant_b}** : {score_b:.4f}")
        st.write(f"**Rang {combattant_a}** : {row_a['Rang']}")
        st.write(f"**Rang {combattant_b}** : {row_b['Rang']}")
        st.write(f"**Ratio {combattant_a}** : {row_a['Ratio']:.3f}")
        st.write(f"**Ratio {combattant_b}** : {row_b['Ratio']:.3f}")




# -------------------------
# Simulation Tournoi
# -------------------------

def proba_victoire(score_a, score_b, k=K):
    return 1 / (1 + np.exp(-k * (score_a - score_b)))


def simuler_combat(row_a, row_b):
    score_a = puissance_combattant(row_a)
    score_b = puissance_combattant(row_b)

    p_a = proba_victoire(score_a, score_b)

    # On retourne directement le nom du combattant
    return row_a.name if random.random() < p_a else row_b.name



def simuler_tournoi(df):
    # Liste des combattants
    combattants = df["Combattant"].tolist()
    random.shuffle(combattants)

    # Mapping rapide nom -> ligne df
    lookup = df.set_index("Combattant")

    while len(combattants) > 1:
        prochain_tour = []

        # Gestion des byes
        if len(combattants) % 2 == 1:
            prochain_tour.append(combattants.pop())

        for i in range(0, len(combattants), 2):
            a = combattants[i]
            b = combattants[i + 1]

            vainqueur = simuler_combat(
                lookup.loc[a],
                lookup.loc[b]
            )
            prochain_tour.append(vainqueur)

        combattants = prochain_tour

    return combattants[0]  # vainqueur final


N_SIMULATIONS = 1000

resultats = []

for _ in range(N_SIMULATIONS):
    vainqueur = simuler_tournoi(df)
    resultats.append(vainqueur)


# -------------------------
# Analyse resultat
# -------------------------


compteur = Counter(resultats)

df_resultats = (
    pd.DataFrame.from_dict(compteur, orient="index", columns=["Victoires"])
      .reset_index()
      .rename(columns={"index": "Combattant"})
)

df_resultats["Probabilite_victoire"] = (
    df_resultats["Victoires"] / N_SIMULATIONS
)

df_resultats = df_resultats.sort_values(
    "Probabilite_victoire", ascending=False
)


st.header("🏆 Simulation du tournoi – 100 runs")

st.dataframe(
    df_resultats.style.format({
        "Probabilite_victoire": "{:.1%}"
    }),
    use_container_width=True,
    hide_index=True
)
