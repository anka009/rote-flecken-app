import streamlit as st
from PIL import Image, ImageDraw
import numpy as np

# 📁 Bild hochladen
uploaded_file = st.file_uploader("📁 Lade ein Bild hoch", type=["jpg", "jpeg", "png", "tif", "tiff"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Originalbild", use_column_width=True)

    st.markdown("### ➕ Flecken manuell markieren")

    # 📍 Koordinaten-Eingabe
    x = st.slider("X-Koordinate", 0, image.width, value=image.width // 2)
    y = st.slider("Y-Koordinate", 0, image.height, value=image.height // 2)

    # 🔴 Fleck zeichnen
    draw = ImageDraw.Draw(image)
    radius = 10
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="red")

    st.image(image, caption="🟥 Markierter Fleck", use_column_width=True)

    # 📦 Koordinaten speichern
    if "punkte" not in st.session_state:
        st.session_state.punkte = []

    if st.button("📌 Punkt speichern"):
        st.session_state.punkte.append((x, y))
        st.success(f"Punkt gespeichert: ({x}, {y})")

    # 📋 Liste anzeigen
    if st.session_state.punkte:
        st.markdown("### 📋 Gespeicherte Punkte")
        for idx, (px, py) in enumerate(st.session_state.punkte, 1):
            st.write(f"{idx}. X: {px}, Y: {py}")
