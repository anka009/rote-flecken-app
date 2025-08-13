# app_single_view.py — Interaktive Korrektur in einem Bild
import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io
import csv

# Klick-Erfassung
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAVE_CLICK = True
except:
    HAVE_CLICK = False

st.set_page_config(page_title="🖌️ Objekte-Korrektur", layout="wide")
st.title("🖌️ Interaktive Korrektur im Einzelbild")

# Sidebar Einstellungen
st.sidebar.header("Einstellungen")
radius = st.sidebar.slider("Radius der Markierungen (px)", 1, 50, 10)
color_picker = st.sidebar.color_picker("Farbe der Markierung", "#ff0000")
line_thickness = st.sidebar.slider("Linienstärke", 1, 10, 2)

# Upload
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    max_size = (1024, 1024)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    if "points" not in st.session_state:
        st.session_state["points"] = []

    st.write("**Korrektur:** Klicke auf bestehenden Punkt zum Löschen oder auf leeren Bereich zum Hinzufügen.")

    # Klick-Logik
    if HAVE_CLICK:
        coords = streamlit_image_coordinates(img, key="coords")
        if coords:
            x, y = coords["x"], coords["y"]
            removed = False
            for i, (px, py) in enumerate(st.session_state["points"]):
                if (px - x)**2 + (py - y)**2 <= radius**2:
                    st.session_state["points"].pop(i)
                    removed = True
                    break
            if not removed:
                st.session_state["points"].append((x, y))

    # Bild mit Markierungen
    img_array = np.array(img)
    marked = img_array.copy()
    rgb_color = tuple(int(color_picker.lstrip("#")[i:i+2], 16) for i in (0,2,4))
    bgr_color = rgb_color[::-1]
    for (x, y) in st.session_state["points"]:
        cv2.circle(marked, (x, y), radius, bgr_color, line_thickness)

    # Anzeige + Zähler
    st.image(marked, caption=f"Markierte Objekte: {len(st.session_state['points'])}", use_column_width=True)

    # Zurücksetzen
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
