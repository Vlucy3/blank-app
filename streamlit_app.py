import streamlit as st
import pandas as pd
import json
import os
import altair as alt
from transformers import pipeline

# --- 0. NASTAVITVE ---
st.set_page_config(page_title="Analiza Komentarjev", page_icon="🧠", layout="wide")

# --- 1. FUNKCIJE ---

@st.cache_resource
def load_pipeline():
    # 3. Sentiment Analysis: Integrate Transformer model from Hugging Face
    # Uporabimo specifičen model, ki ga zahteva profesor
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

@st.cache_data
def load_data():
    filename = 'data.json'
    if not os.path.exists(filename):
        return None, None, None

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df_products = pd.DataFrame(data['products'])
    
    df_reviews = pd.DataFrame(data['reviews'])
    if not df_reviews.empty:
        df_reviews['date'] = pd.to_datetime(df_reviews['date'])

    df_testimonials = pd.DataFrame(data['testimonials'], columns=['Mnenje'])

    return df_products, df_reviews, df_testimonials

def analiziraj_besedilo(df):
    classifier = load_pipeline()
    labels = []
    scores = []
    
    # Hugging Face pipeline vrne seznam slovarjev
    # Primer: [{'label': 'POSITIVE', 'score': 0.998}]
    
    # Opomba: Za hitrost bi lahko poslali celoten seznam (list(df['comment'])), 
    # ampak zaradi omejitve dolžine (truncation) naredimo zanko za varnost.
    
    for comment in df['comment']:
        # Omejimo na prvih 512 znakov, ker imajo BERT modeli omejitev
        # in da preprečimo napake pri dolgih tekstih.
        text_input = comment[:512]
        
        rezultat = classifier(text_input)[0]
        
        # Shranimo Label (POSITIVE/NEGATIVE) in Score (verjetnost)
        labels.append(rezultat['label'])
        scores.append(rezultat['score'])
    
    df['Sentiment'] = labels
    df['Confidence'] = scores
    
    # Indikatorji za tabelo
    def doloci_barvo(l):
        if l == "POSITIVE": return "🟩"
        elif l == "NEGATIVE": return "🟥"
        else: return "⬜"
    
    df['Stanje'] = df['Sentiment'].apply(doloci_barvo)
    return df

# --- 2. GLAVNI PROGRAM ---

df_products, df_reviews, df_testimonials = load_data()

if df_products is None:
    st.error("Datoteka 'data.json' manjka!")
    st.stop()

st.title("🧠 Pregled in Analiza Komentarjev")

# Sidebar
view_option = st.sidebar.radio("Pogled:", ("Analiza Komentarjev", "Pregled Izdelkov", "Mnenja"))

if view_option == "Analiza Komentarjev":
    
    # Časovnica
    meseci = [
        "Januar 2023", "Februar 2023", "Marec 2023", "April 2023", 
        "Maj 2023", "Junij 2023", "Julij 2023", "Avgust 2023", 
        "September 2023", "Oktober 2023", "November 2023", "December 2023"
    ]
    izbran_mesec = st.select_slider("Izberi obdobje:", options=meseci, value="Januar 2023")
    idx_meseca = meseci.index(izbran_mesec) + 1
    
    df_filtered = df_reviews[
        (df_reviews['date'].dt.month == idx_meseca) & 
        (df_reviews['date'].dt.year == 2023)
    ].copy()
    
    if not df_filtered.empty:
        # Analiza
        with st.spinner('Model analizira sentiment...'):
            df_analizirano = analiziraj_besedilo(df_filtered)
        
        # KPI
        st.divider()
        col1, col2, col3 = st.columns(3)
        stevilo_vseh = len(df_analizirano)
        stevilo_poz = len(df_analizirano[df_analizirano['Sentiment'] == 'POSITIVE'])
        stevilo_neg = len(df_analizirano[df_analizirano['Sentiment'] == 'NEGATIVE'])
        
        col1.metric("Število komentarjev", stevilo_vseh)
        col2.metric("Pozitivni (POSITIVE)", f"{stevilo_poz}")
        col3.metric("Negativni (NEGATIVE)", f"{stevilo_neg}")
        
        # --- 4. VISUALIZATION (BAR CHART) ---
        col_chart, col_data = st.columns([1, 2])
        
        with col_chart:
            st.markdown("#### Sentiment & Povprečna Samozavest")
            
            # Priprava podatkov za graf:
            # Štejemo pojavitve (count) in povprečje samozavesti (mean score)
            chart_data = df_analizirano.groupby('Sentiment').agg(
                Count=('Sentiment', 'count'),
                AvgConfidence=('Confidence', 'mean')
            ).reset_index()
            
            # Bar Chart z Altair
            bar_chart = alt.Chart(chart_data).mark_bar().encode(
                x=alt.X('Sentiment', axis=alt.Axis(title="Sentiment")),
                y=alt.Y('Count', axis=alt.Axis(title="Število komentarjev")),
                color=alt.Color('Sentiment', scale=alt.Scale(
                    domain=['POSITIVE', 'NEGATIVE'],
                    range=['#2ecc71', '#e74c3c'] 
                )),
                # Advanced: Tooltip z Average Confidence Score
                tooltip=[
                    'Sentiment', 
                    'Count', 
                    alt.Tooltip('AvgConfidence', format='.2%', title="Povpr. samozavest (Score)")
                ]
            ).properties(height=300)
            
            st.altair_chart(bar_chart, use_container_width=True)

        with col_data:
            st.markdown("#### Podrobnosti")
            
            st.dataframe(
                df_analizirano,
                use_container_width=True,
                column_config={
                    "Stanje": st.column_config.TextColumn("AI", width="small"),
                    "date": st.column_config.DateColumn("Datum", format="DD.MM"),
                    "comment": "Komentar",
                    "Sentiment": st.column_config.TextColumn("Ocena"),
                    # Prikaz samozavesti kot progress bar
                    "Confidence": st.column_config.ProgressColumn(
                        "Confidence Score", 
                        min_value=0, 
                        max_value=1, 
                        format="%.2f"
                    )
                },
                column_order=["Stanje", "Sentiment", "Confidence", "comment"]
            )
    else:
        st.info(f"V mesecu {izbran_mesec} ni bilo komentarjev.")

elif view_option == "Pregled Izdelkov":
    st.header("🛒 Izdelki")
    st.dataframe(df_products, use_container_width=True)

elif view_option == "Mnenja":
    st.header("💬 Mnenja")
    st.table(df_testimonials)