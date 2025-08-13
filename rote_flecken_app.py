# app.py — Interaktiver Objekte-Zähler mit TIFF-Unterstützung
import streamlit as st
from PIL import Image
import numpy as np
import io
import csv

# optional: Klick-Erfassung
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAVE_CLICK = True
except Exception:
    HAVE_CLICK = False

st.set_page_config(page_title="🖌️ Interaktiver Objekte-Zähler", layout="wide")
st.title("🖌️ Interaktiver Objekte-Zähler — Stufe 3.0")

# Sidebar Einstellungen
st.sidebar.header("Einstellungen für Markierung")
radius = st.sidebar.slider("Radius der Markierungen (px)", 1, 50, 10)
color_picker = st.sidebar.color_picker("Farbe der Markierung", "#ff0000")
line_thickness = st.sidebar.slider("Linienstärke", 1, 10, 2)

# Upload
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if uploaded_file:
    # Bild laden und in RGB konvertieren
    img = Image.open(uploaded_file).convert("RGB")
    
    # Optional: skalieren, falls sehr groß
    max_size = (1024, 1024)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Session-State für Punkte
    if "points" not in st.session_state:
        st.session_state["points"] = []

    st.write("**Markiere die Objekte:** Klicke auf das Bild, um Punkte hinzuzufügen.")
    
    # Interaktive Bildanzeige und Klick
    if HAVE_CLICK:
        coords = streamlit_image_coordinates(img, key="coords")
        if coords:
            x, y = coords["x"], coords["y"]
            # Punkt hinzufügen
            st.session_state["points"].append((x, y))
    
    # Bild mit Markierungen anzeigen
    img_array = np.array(img)
    import cv2
    marked = img_array.copy()
    rgb_color = tuple(int(color_picker.lstrip("#")[i:i+2], 16) for i in (0,2,4))
    bgr_color = rgb_color[::-1]
    for (x, y) in st.session_state["points"]:
        cv2.circle(marked, (x,y), radius, bgr_color, line_thickness)
    
    # Zwei Spalten: Original + Markiert
    col1, col2 = st.columns(2)
    col1.image(img, caption="Original", use_column_width=True)
    col2.image(marked, caption=f"Markierte Objekte: {len(st.session_state['points'])}", use_column_width=True)

    # Punkte zurücksetzen
    if st.button("🔄 Alle Punkte zurücksetzen"):
        st.session_state["points"] = []

    # CSV-Export
    if st.session_state["points"]:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["x","y"])
        for p in st.session_state["points"]:
            writer.writerow(p)
        st.download_button("📥 Punkte als CSV exportieren", data=buf.getvalue().encode("utf-8"), file_name="punkte.csv", mime="text/csv")
