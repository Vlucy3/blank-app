import streamlit as st
import pandas as pd
import json
import os
import altair as alt

# --- 0. NASTAVITVE ---
st.set_page_config(page_title="Analiza Komentarjev", page_icon="🧠", layout="wide")

# --- 1. FUNKCIJE ---

@st.cache_data
def load_data():
    # Najprej poskusimo naložiti analizirano datoteko
    filename = 'data_analizirano.json'
    
    # Če analizirana ne obstaja, vzamemo original (backup)
    if not os.path.exists(filename):
        filename = 'data.json'
        st.warning("Uporabljam 'data.json' (neanalizirano), ker 'data_analizirano.json' manjka.")
    
    if not os.path.exists(filename):
        return None, None, None

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df_products = pd.DataFrame(data['products'])
    
    df_reviews = pd.DataFrame(data['reviews'])
    if not df_reviews.empty:
        df_reviews['date'] = pd.to_datetime(df_reviews['date'])
        
        # Če imamo sentiment, določimo barve
        if 'Sentiment' in df_reviews.columns:
            def doloci_barvo(l):
                if l == "POSITIVE": return "🟩"
                elif l == "NEGATIVE": return "🟥"
                else: return "⬜"
            df_reviews['Stanje'] = df_reviews['Sentiment'].apply(doloci_barvo)
        else:
            # Če ni analize, so vsi "sivi"
            df_reviews['Stanje'] = "⬜"
            df_reviews['Sentiment'] = "Ni podatka"
            df_reviews['Confidence'] = 0.0

    df_testimonials = pd.DataFrame(data['testimonials'], columns=['Mnenje'])

    return df_products, df_reviews, df_testimonials

# --- 2. GLAVNI PROGRAM ---

df_products, df_reviews, df_testimonials = load_data()

if df_reviews is None:
    st.error("Nobena datoteka s podatki ne obstaja!")
    st.stop()

st.title("🧠 Pregled in Analiza Komentarjev")

# Sidebar
view_option = st.sidebar.radio("Pogled:", ("Analiza Komentarjev", "Pregled Izdelkov", "Mnenja"))

if view_option == "Analiza Komentarjev":
    
    # Preverimo, če je bila analiza opravljena (t.j. ali imamo stolpec Confidence > 0)
    ima_analizo = df_reviews['Confidence'].sum() > 0

    if not ima_analizo:
        st.warning("⚠️ Prikazujem surove podatke. Za analizo sentimenta zaženi 'priprava_podatkov.py' lokalno in naloži 'data_analizirano.json'.")

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
        # KPI
        st.divider()
        col1, col2, col3 = st.columns(3)
        stevilo_vseh = len(df_filtered)
        
        if ima_analizo:
            stevilo_poz = len(df_filtered[df_filtered['Sentiment'] == 'POSITIVE'])
            stevilo_neg = len(df_filtered[df_filtered['Sentiment'] == 'NEGATIVE'])
        else:
            stevilo_poz = 0
            stevilo_neg = 0
        
        col1.metric("Število komentarjev", stevilo_vseh)
        col2.metric("Pozitivni", f"{stevilo_poz}")
        col3.metric("Negativni", f"{stevilo_neg}")
        
        # --- GRAF (Samo če imamo analizo) ---
        col_chart, col_data = st.columns([1, 2])
        
        with col_chart:
            if ima_analizo:
                st.markdown("#### Sentiment")
                chart_data = df_filtered.groupby('Sentiment').agg(
                    Count=('Sentiment', 'count'),
                    AvgConfidence=('Confidence', 'mean')
                ).reset_index()
                
                bar_chart = alt.Chart(chart_data).mark_bar().encode(
                    x=alt.X('Sentiment', axis=alt.Axis(title="Sentiment")),
                    y=alt.Y('Count', axis=alt.Axis(title="Število")),
                    color=alt.Color('Sentiment', scale=alt.Scale(domain=['POSITIVE', 'NEGATIVE'], range=['#2ecc71', '#e74c3c'])),
                    tooltip=['Sentiment', 'Count', alt.Tooltip('AvgConfidence', format='.2%')]
                ).properties(height=300)
                st.altair_chart(bar_chart, use_container_width=True)
            else:
                st.info("Graf sentimenta ni na voljo (manjkajo analizirani podatki).")

        with col_data:
            st.markdown("#### Podrobnosti")
            
            prikazni_stolpci = ['Stanje', 'date', 'comment']
            if ima_analizo:
                prikazni_stolpci = ['Stanje', 'Sentiment', 'Confidence', 'comment']

            config = {
                "date": st.column_config.DateColumn("Datum", format="DD.MM"),
                "comment": "Komentar"
            }
            if ima_analizo:
                 config["Confidence"] = st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1, format="%.2f")

            st.dataframe(
                df_filtered[prikazni_stolpci],
                use_container_width=True,
                column_config=config
            )
    else:
        st.info(f"V mesecu {izbran_mesec} ni bilo komentarjev.")

elif view_option == "Pregled Izdelkov":
    st.header("🛒 Izdelki")
    st.dataframe(df_products, use_container_width=True)

elif view_option == "Mnenja":
    st.header("💬 Mnenja")
    st.table(df_testimonials)