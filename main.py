import streamlit as st
import pandas as pd
from pathlib import Path

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
