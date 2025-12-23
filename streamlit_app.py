import streamlit as st
import pandas as pd
import json
import os
import altair as alt  # Knjižnica za grafe
from transformers import pipeline

# --- 1. KONFIGURACIJA IN AI MODEL ---

@st.cache_resource
def load_sentiment_model():
    """
    Naloži AI model. Shrani se v cache za hitrejše delovanje.
    """
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# --- 2. NALAGANJE PODATKOV ---
def load_data():
    filename = 'data.json'
    if not os.path.exists(filename):
        st.error(f"Datoteka '{filename}' ni bila najdena.")
        return None, None, None

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df_products = pd.DataFrame(data['products'])
    
    df_reviews = pd.DataFrame(data['reviews'])
    if not df_reviews.empty:
        df_reviews['date'] = pd.to_datetime(df_reviews['date'])

    df_testimonials = pd.DataFrame(data['testimonials'], columns=['Mnenje'])

    return df_products, df_reviews, df_testimonials

df_products, df_reviews, df_testimonials = load_data()

if df_products is None:
    st.stop()

# --- 3. VMESNIK (LAYOUT) ---

st.title("📊 Pregled in Analiza Podatkov")

# Sidebar
st.sidebar.header("Navigacija")
view_option = st.sidebar.radio(
    "Izberi pogled:",
    ("Izdelki (Products)", "Pričevanja (Testimonials)", "Ocene (Reviews)")
)
st.sidebar.markdown("---")

# --- LOGIKA PRIKAZA ---

# A. IZDELKI
if view_option == "Izdelki (Products)":
    st.header("Seznam Izdelkov")
    st.dataframe(
        df_products, 
        use_container_width=True,
        column_config={"price": st.column_config.NumberColumn("Cena (€)", format="€ %s")}
    )

# B. PRIČEVANJA
elif view_option == "Pričevanja (Testimonials)":
    st.header("Mnenja uporabnikov")
    st.table(df_testimonials)

# C. OCENE (Analiza + GRAF)
elif view_option == "Ocene (Reviews)":
    st.header("Analiza Sentimentov")
    
    # Slider
    months = [
        "Januar 2023", "Februar 2023", "Marec 2023", "April 2023", 
        "Maj 2023", "Junij 2023", "Julij 2023", "Avgust 2023", 
        "September 2023", "Oktober 2023", "November 2023", "December 2023"
    ]
    selected_month_name = st.select_slider("Izberi mesec (leto 2023):", options=months)
    month_index = months.index(selected_month_name) + 1
    
    # Filtriranje
    filtered_df = df_reviews[
        (df_reviews['date'].dt.month == month_index) & 
        (df_reviews['date'].dt.year == 2023)
    ].copy()
    
    filtered_df = filtered_df.sort_values(by='date', ascending=False)

    st.subheader(f"Rezultati za: {selected_month_name}")
    
    if not filtered_df.empty:
        # --- ZAGON AI ANALIZE ---
        with st.spinner("🧠 Umetna inteligenca analizira komentarje..."):
            classifier = load_sentiment_model()
            results = classifier(filtered_df['comment'].str[:512].tolist())
        
        # --- OBDELAVA REZULTATOV ---
        sentiment_labels = [res['label'] for res in results]
        sentiment_scores = [res['score'] for res in results]
        
        # Dodamo podatke v DataFrame
        filtered_df['Sentiment'] = sentiment_labels
        filtered_df['Score'] = sentiment_scores
        
        # Ustvarimo indikatorje (kvadratke)
        filtered_df['Indikator'] = filtered_df['Sentiment'].apply(lambda x: "🟩" if x == "POSITIVE" else "🟥")

        # -------------------------------------------------------
        # TUKAJ JE KODA ZA GRAF (ALTAIR)
        # -------------------------------------------------------
        st.markdown("### 📈 Statistika sentimenta")
        
        # Priprava podatkov za graf (Grouping)
        chart_data = filtered_df.groupby('Sentiment').agg(
            Count=('Sentiment', 'count'),      # Preštejemo koliko je katerih
            Avg_Score=('Score', 'mean')        # Izračunamo povprečno zanesljivost
        ).reset_index()

        # Izris grafa
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Sentiment', title='Sentiment'),
            y=alt.Y('Count', title='Število ocen'),
            # Barve: Zelena za POSITIVE, Rdeča za NEGATIVE
            color=alt.Color('Sentiment', scale=alt.Scale(domain=['POSITIVE', 'NEGATIVE'], range=['#2ecc71', '#e74c3c']), legend=None),
            # Tooltip (kaj se pokaže, ko greš z miško čez)
            tooltip=[
                alt.Tooltip('Sentiment', title='Sentiment'),
                alt.Tooltip('Count', title='Število'),
                alt.Tooltip('Avg_Score', format='.2%', title='Povpr. zanesljivost')
            ]
        ).properties(
            height=300 # Višina grafa
        )

        st.altair_chart(chart, use_container_width=True)
        # -------------------------------------------------------

        # --- PRIKAZ TABELE ---
        st.markdown("### 📝 Podrobni podatki")
        st.dataframe(
            filtered_df,
            use_container_width=True,
            column_config={
                "Indikator": st.column_config.TextColumn("Stanje", width="small"),
                "date": st.column_config.DateColumn("Datum", format="DD.MM.YYYY"),
                "comment": "Komentar",
                "Sentiment": st.column_config.TextColumn("Ocena AI"),
                "Score": st.column_config.ProgressColumn("Zanesljivost", format="%.2f", min_value=0.5, max_value=1.0)
            },
            column_order=["Indikator", "date", "comment", "Sentiment", "Score"]
        )

    else:
        st.warning(f"Za mesec {selected_month_name} ni bilo najdenih nobenih ocen.")