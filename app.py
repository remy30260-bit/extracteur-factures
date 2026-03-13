import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz
from PIL import Image
import io

st.set_page_config(page_title="Extracteur de Factures", page_icon="🧾", layout="wide")

st.title("🧾 Extracteur de Factures")
st.markdown("Uploadez vos factures (PDF ou image) → extraction automatique des données")

api_key = st.sidebar.text_input("🔑 Clé API Gemini", type="password")

if api_key:
    genai.configure(api_key=api_key)

def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images

def extraire_donnees(image, model):
    prompt = """
    Analyse cette facture et extrais les informations suivantes en JSON uniquement.
    Réponds UNIQUEMENT avec le JSON, rien d'autre.
    
    {
       "fournisseur_client": "nom du fournisseur qui ÉMET la facture (celui qui vend / qui demande le paiement), PAS le client qui reçoit la facture",
        "numero_facture": "numéro de facture",
        "type": "type de document : Facture / Avoir / Note de frais / Facture pro-forma",
        "montant_facture": "montant TTC total de la facture",
        "date_facture": "date de la facture ou date du fait générateur"
    }
    
    Si une information est absente, mets null.
    """
    
    response = model.generate_content([prompt, image])
    text = response.text.strip()
    
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
