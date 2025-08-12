import streamlit as st
from PIL import Image, ImageDraw, ImageEnhance
import numpy as np

st.set_page_config(layout="wide")
st.title("🧪 Rote Flecken App – Erweiterte Version")

# 📁 Bild hochladen
uploaded_file = st.file_uploader("📁 Bild hochladen", type=["jpg", "jpeg", "png", "tif", "tiff"])
if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")

    # 🌓 Kontrastregler
    kontrast = st.slider("🌓 Kontrast", 0.5, 3.0, 1.0, 0.1)
    image = ImageEnhance.Contrast(image).enhance(kontrast)

    # 📏 Markierungsdicke
    radius = st.slider("📏 Markierungsradius", 5, 30, 10)

    # 🎚️ Schwellenwert für automatische Erkennung
    threshold = st.slider("🎚️ Schwellenwert (Helligkeit)", 0, 255, 100)

    # 🧠 Session-Initialisierung
    if "punkte" not in st.session_state:
        st.session_state.punkte = []
    if "farben" not in st.session_state:
        st.session_state.farben = []

    # ✏️ Manuelle Markierung
    st.markdown("### ➕ Manuelle Fleckenmarkierung")
    x = st.slider("X", 0, image.width, value=image.width // 2)
    y = st.slider("Y", 0, image.height, value=image.height // 2)
    farbe = st.radio("Farbe", ["Rot", "Grün", "Blau", "Dunkel"])

    if st.button("📌 Punkt speichern"):
        st.session_state.punkte.append((x, y))
        st.session_state.farben.append(farbe)
        st.success(f"Gespeichert: ({x}, {y}) – {farbe}")

    # ❌ Punkt entfernen
    st.markdown("### ❌ Punkt entfernen")
    if st.session_state.punkte:
        idx_to_remove = st.number_input("Index löschen", min_value=1, max_value=len(st.session_state.punkte), step=1)
        if st.button("🗑️ Löschen"):
            st.session_state.punkte.pop(idx_to_remove - 1)
            st.session_state.farben.pop(idx_to_remove - 1)
            st.experimental_rerun()

    # 🧪 Automatische Fleckenerkennung
    st.markdown("### 🧪 Automatische Fleckenerkennung")
    gray = np.array(image.convert("L"))
    mask = gray < threshold
    coords = np.column_stack(np.where(mask))

    # 🖼️ Bild zeichnen
    image_draw = image.copy()
    draw = ImageDraw.Draw(image_draw)
    farbcode = {"Rot": "red", "Grün": "green", "Blau": "blue", "Dunkel": "black"}

    # Manuelle Punkte
    for (px, py), f in zip(st.session_state.punkte, st.session_state.farben):
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=farbcode[f])

    # Automatische Punkte (blau)
    for y, x in coords[::100]:  # Nur jeden 100. Punkt
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="blue")

    st.image(image_draw, caption="🖼️ Bild mit Flecken", use_column_width=True)

    # 📊 Zähler
    st.markdown("### 📊 Fleckenanzahl")
    for f in ["Rot", "Grün", "Blau", "Dunkel"]:
        st.metric(f"{f}e Flecken", st.session_state.farben.count(f))
    st.metric("🔵 Automatisch erkannte Flecken", len(coords[::100]))

    # 📋 Punktliste
    st.markdown("### 📋 Gespeicherte Punkte")
    for idx, ((px, py), f) in enumerate(zip(st.session_state.punkte, st.session_state.farben), 1):
        st.write(f"{idx}. X: {px}, Y: {py}, Farbe: {f}")
