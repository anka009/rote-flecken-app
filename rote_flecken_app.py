# fleck_lernen_app_form.py
import streamlit as st
from PIL import Image
import numpy as np
import cv2
import json
from pathlib import Path

# ================================
# Lokale DB-Datei
# ================================
DB_FILE = Path("fleck_db.json")
if DB_FILE.exists():
    with open(DB_FILE, "r") as f:
        fleck_db = json.load(f)
else:
    fleck_db = []

# ================================
# Streamlit Setup
# ================================
st.set_page_config(page_title="🎯 Fleck-Lernen mit Formanalyse", layout="wide")
st.title("🎯 Interaktive Fleck-Lern- & Analyse-App mit Formparametern")

# Sidebar Parameter
radius_toleranz = st.sidebar.slider("Toleranz Durchmesser (%)", 0, 50, 20)
farbe_toleranz = st.sidebar.slider("Toleranz Farbwert HSV (%)", 0, 50, 20)
form_toleranz = st.sidebar.slider("Toleranz Form (%)", 0, 50, 15)
min_radius_auto = st.sidebar.slider("Minimaler Radius für Auto-Erkennung (px)", 1, 100, 5)

# Upload
uploaded_file = st.file_uploader("Bild hochladen", type=["png","jpg","jpeg","tif","tiff"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)
    img_display = img_np.copy()

    try:
        from streamlit_image_coordinates import streamlit_image_coordinates
        coords = streamlit_image_coordinates(img, key="click")
    except:
        st.error("⚠ Bitte installiere 'streamlit-image-coordinates' per `pip install streamlit-image-coordinates`")
        coords = None

    # ================================
    # Fleckparameter-Funktion
    # ================================
    def finde_fleck_parameter(x, y, img_array):
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            if cv2.pointPolygonTest(cnt, (x, y), False) >= 0:
                area = cv2.contourArea(cnt)
                if area == 0:
                    continue
                perimeter = cv2.arcLength(cnt, True)
                diameter = np.sqrt(4 * area / np.pi)

                # Form-Parameter
                roundness = (4 * np.pi * area) / (perimeter ** 2 + 1e-6)

                # Ellipse für Exzentrizität
                if len(cnt) >= 5:
                    ellipse = cv2.fitEllipse(cnt)
                    a = max(ellipse[1]) / 2  # große Halbachse
                    b = min(ellipse[1]) / 2  # kleine Halbachse
                    exzentrizitaet = np.sqrt(1 - (b ** 2 / a ** 2))
                else:
                    exzentrizitaet = 0

                # Mittlere HSV-Farbe
                mask = np.zeros(gray.shape, np.uint8)
                cv2.drawContours(mask, [cnt], -1, 255, -1)
                mean_color = cv2.mean(cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV), mask=mask)
                h, s, v, _ = mean_color

                return {
                    "durchmesser": diameter,
                    "farbe_h": h,
                    "farbe_s": s,
                    "farbe_v": v,
                    "flaeche": area,
                    "rundheit": roundness,
                    "exzentrizitaet": exzentrizitaet
                }
        return None

    # Klick verarbeitet → Parameter speichern
    if coords:
        params = finde_fleck_parameter(coords["x"], coords["y"], img_np)
        if params:
            fleck_db.append(params)
            with open(DB_FILE, "w") as f:
                json.dump(fleck_db, f, indent=2)
            st.success(f"✅ Neuer Fleck gelernt: {params}")
        else:
            st.warning("⚠ Kein Fleck an dieser Stelle gefunden.")

    # ================================
    # Vergleich mit gelernten Daten
    # ================================
    def passt_zu_gelernten(param):
        for g in fleck_db:
            if abs(param["durchmesser"] - g["durchmesser"]) <= (g["durchmesser"] * radius_toleranz / 100):
                if abs(param["farbe_h"] - g["farbe_h"]) <= (g["farbe_h"] * farbe_toleranz / 100 + 1):
                    if abs(param["rundheit"] - g["rundheit"]) <= (g["rundheit"] * form_toleranz / 100 + 0.01):
                        return True
        return False

    # ================================
    # Auto-Erkennung
    # ================================
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    count_auto = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area == 0:
            continue
        diameter = np.sqrt(4 * area / np.pi)
        if diameter < min_radius_auto:
            continue

        perimeter = cv2.arcLength(cnt, True)
        roundness = (4 * np.pi * area) / (perimeter ** 2 + 1e-6)
        if len(cnt) >= 5:
            ellipse = cv2.fitEllipse(cnt)
            a = max(ellipse[1]) / 2
            b = min(ellipse[1]) / 2
            exzentrizitaet = np.sqrt(1 - (b ** 2 / a ** 2))
        else:
            exzentrizitaet = 0

        mask = np.zeros(gray.shape, np.uint8)
        cv2.drawContours(mask, [cnt], -1, 255, -1)
        mean_color = cv2.mean(cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV), mask=mask)
        h, s, v, _ = mean_color

        param = {
            "durchmesser": diameter,
            "farbe_h": h,
            "farbe_s": s,
            "farbe_v": v,
            "flaeche": area,
            "rundheit": roundness,
            "exzentrizitaet": exzentrizitaet
        }

        if passt_zu_gelernten(param):
            count_auto += 1
            cv2.drawContours(img_display, [cnt], -1, (0, 255, 0), 2)

    # ================================
    # Anzeige
    # ================================
    st.image(img_display, caption=f"Automatisch erkannte Flecke: {count_auto}", use_column_width=True)
    st.write(f"📦 Gelerntes Profil: {len(fleck_db)} Fleck-Typen gespeichert.")
    if st.button("🗑 Datenbank leeren"):
        fleck_db = []
        with open(DB_FILE, "w") as f:
            json.dump(fleck_db, f)
        st.warning("Datenbank geleert.")
