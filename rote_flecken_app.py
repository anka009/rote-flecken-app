# app.py — Interaktiver Objekte-Zähler in einem Bild
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import io
import csv

# Optional: klickbare Koordinaten
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAVE_CLICK = True
except ImportError:
    HAVE_CLICK = False

st.set_page_config(page_title="🖌️ Interaktiver Objekte-Zähler", layout="wide")
st.title("🖌️ Interaktiver Objekte-Zähler — Alles in einem Bild")

# Session State initialisieren
if "points" not in st.session_state:
    st.session_state.points = []

# Bild hochladen
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    img_w, img_h = img.size

    # Parameter für Markierung
    st.sidebar.header("Einstellungen für Markierung")
    radius = st.sidebar.slider("Radius der Markierung (px)", 2, 50, 10)
    color = st.sidebar.color_picker("Farbe der Markierung", "#ff0000")
    thickness = st.sidebar.slider("Linienstärke", 1, 10, 2)

    # Farbe in RGB
    rgb_color = tuple(int(color.lstrip("#")[i:i+2],16) for i in (0,2,4))

    st.markdown("**Markiere die Objekte direkt im Bild.**")
    st.markdown("🔹 Klick auf bestehenden Punkt löscht ihn, Klick auf leeren Bereich fügt neuen Punkt hinzu.")

    # Aktuelles Bild kopieren
    display_img = img.copy()
    draw = ImageDraw.Draw(display_img)
    for x,y in st.session_state.points:
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline=rgb_color, width=thickness)

    # Klickverarbeitung
    if HAVE_CLICK:
        coords = streamlit_image_coordinates(display_img, key="img_coords")
        if coords:
            cx, cy = coords["x"], coords["y"]
            # prüfen, ob Klick innerhalb eines bestehenden Punktes -> löschen
            removed = False
            for i, (px, py) in enumerate(st.session_state.points):
                if (px-cx)**2 + (py-cy)**2 <= radius**2:
                    st.session_state.points.pop(i)
                    removed = True
                    break
            if not removed:
                st.session_state.points.append((cx, cy))
            # Bild direkt aktualisieren
            display_img = img.copy()
            draw = ImageDraw.Draw(display_img)
            for x,y in st.session_state.points:
                draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline=rgb_color, width=thickness)

    st.image(display_img, caption=f"Gefundene Objekte: {len(st.session_state.points)}", use_column_width=True)

    # CSV Download
    if st.session_state.points:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["x","y"])
        for x,y in st.session_state.points:
            writer.writerow([x,y])
        csv_bytes = buf.getvalue().encode("utf-8")
        st.download_button("📥 Punkte als CSV herunterladen", data=csv_bytes, file_name="punkte.csv", mime="text/csv")
else:
    st.info("Bitte zuerst ein Bild hochladen.")
