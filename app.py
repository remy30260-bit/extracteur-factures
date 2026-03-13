import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import fitz  # pymupdf
from PIL import Image
import io

st.set_page_config(page_title="Extracteur de Factures", page_icon="🧾", layout="wide")

st.title("🧾 Extracteur de Factures")
st.markdown("Uploadez vos factures (PDF ou image) → extraction automatique des données")

# Clé API
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
        "fournisseur": "nom du fournisseur",
        "numero_facture": "numéro de facture",
        "date_facture": "date de la facture",
        "date_echeance": "date d'échéance si présente",
        "montant_ht": "montant hors taxes",
        "tva": "montant TVA",
        "montant_ttc": "montant total TTC",
        "devise": "devise (EUR, USD...)",
        "client": "nom du client/destinataire",
        "description": "description courte des produits/services"
    }
    
    Si une information est absente, mets null.
    """
    
    response = model.generate_content([prompt, image])
    text = response.text.strip()
    
    # Nettoyer le JSON
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    
    return json.loads(text)

# Upload fichiers
fichiers = st.file_uploader(
    "📁 Uploadez vos factures",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if fichiers and api_key:
    if st.button("🚀 Extraire les données", type="primary"):
        model = genai.GenerativeModel("gemini-1.5-flash")
        resultats = []
        
        progress = st.progress(0)
        status = st.empty()
        
        for i, fichier in enumerate(fichiers):
            status.text(f"Traitement : {fichier.name}...")
            
            try:
                images = []
                
                if fichier.type == "application/pdf":
                    images = pdf_to_images(fichier.read())
                else:
                    images = [Image.open(fichier)]
                
                # On prend la première page
                donnees = extraire_donnees(images[0], model)
                donnees["fichier"] = fichier.name
                donnees["statut"] = "✅ OK"
                resultats.append(donnees)
                
            except Exception as e:
                resultats.append({
                    "fichier": fichier.name,
                    "statut": f"❌ Erreur: {str(e)}"
                })
            
            progress.progress((i + 1) / len(fichiers))
        
        status.text("✅ Traitement terminé !")
        
        # Affichage résultats
        df = pd.DataFrame(resultats)
        
        # Réorganiser colonnes
        cols = ["fichier", "statut", "fournisseur", "numero_facture", 
                "date_facture", "date_echeance", "montant_ht", 
                "tva", "montant_ttc", "devise", "client", "description"]
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
        
        st.dataframe(df, use_container_width=True)
        
        # Export Excel
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        
        st.download_button(
            label="📥 Télécharger Excel",
            data=buffer,
            file_name="factures_extraites.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif fichiers and not api_key:
    st.warning("⚠️ Entrez votre clé API Gemini dans le menu à gauche")

elif not fichiers:
    st.info("👆 Uploadez vos factures pour commencer")
