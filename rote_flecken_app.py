import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import io

st.set_page_config(page_title="🖌️ Interaktiver Objekte-Zähler", layout="wide")
st.title("🖌️ Interaktiver Objekte-Zähler — Nebeneinander")

st.sidebar.header("Einstellungen für Markierung")
radius = st.sidebar.slider("Radius der Markierungen (px)", 1, 50, 10)
color = st.sidebar.color_picker("Farbe der Markierung", "#FF0000")
line_width = st.sidebar.slider("Linienstärke", 1, 10, 2)

uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)

    # Session-State für Punkte
    if "points" not in st.session_state:
        st.session_state.points = []

    st.markdown("**Klicke auf Koordinaten, um Punkte hinzuzufügen**")

    col1, col2 = st.columns(2)

    # Linkes Bild: Original + Klickbereich
    with col1:
        st.image(img, caption="Original", use_column_width=True)
        x = st.number_input("X hinzufügen", 0, img.width-1, step=1)
        y = st.number_input("Y hinzufügen", 0, img.height-1, step=1)
        if st.button("Punkt hinzufügen"):
            st.session_state.points.append((x, y, radius))

    # Rechtes Bild: Markierte Punkte
    marked = img.copy()
    draw = ImageDraw.Draw(marked)
    for px, py, pr in st.session_state.points:
        draw.ellipse([px-pr, py-pr, px+pr, py+pr], outline=color, width=line_width)

    with col2:
        st.image(marked, caption=f"Markierungen ({len(st.session_state.points)})", use_column_width=True)

    # CSV Export
    import csv
    import io
    if st.session_state.points:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["x","y","radius"])
        for p in st.session_state.points:
            writer.writerow(p)
        st.download_button("📥 CSV exportieren", data=buf.getvalue().encode("utf-8"), file_name="punkte.csv")
