import json
from transformers import pipeline
import pandas as pd

# 1. Naložimo originalne podatke
print("Nalaganje podatkov...")
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

reviews = data['reviews']

# 2. Pripravimo model (Točno ta, ki ga zahteva naloga)
print("Nalaganje modela (to lahko traja minutko)...")
classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# 3. Analiziramo vsak komentar
print(f"Analiziram {len(reviews)} komentarjev...")

for i, review in enumerate(reviews):
    text = review['comment']
    # Omejimo na 512 znakov zaradi omejitve modela
    text_input = text[:512]
    
    # Izvedemo analizo
    rezultat = classifier(text_input)[0]
    
    # Rezultate ZAPIŠEMO direktno v podatke
    review['Sentiment'] = rezultat['label']
    review['Confidence'] = rezultat['score']
    
    if i % 10 == 0:
        print(f"Obdelano: {i}/{len(reviews)}")

# 4. Shranimo v NOVO datoteko
output_filename = 'data_analizirano.json'
with open(output_filename, 'w', encoding='utf-8') as f:
    # Shranimo celotno strukturo (products, testimonials in sedaj analizirane reviews)
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Končano! Ustvarjena je datoteka '{output_filename}'.")
print("Sedaj naloži to datoteko na GitHub/Render.")