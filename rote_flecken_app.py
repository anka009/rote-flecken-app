# app.py — Interaktiver Objekte-Zähler mit TIFF-Unterstützung
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io
import csv

st.set_page_config(page_title="🖌️ Interaktiver Objekte-Zähler", layout="wide")
st.title("🖌️ Interaktiver Objekte-Zähler")

# ---------------- Sidebar: Einstellungen ----------------
st.sidebar.header("Einstellungen für Markierung")
radius = st.sidebar.slider("Radius der Markierungen (px)", 1, 50, 10)
stroke_width = st.sidebar.slider("Linienstärke", 1, 10, 2)
stroke_color = st.sidebar.color_picker("Farbe der Markierung", "#FF0000")

# ---------------- Bild hochladen ----------------
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", 
                                 type=["png","jpg","jpeg","tif","tiff"])

if uploaded_file:
    # Bild laden & auf RGB konvertieren
    img = Image.open(uploaded_file).convert("RGB")
    max_size = (1024, 1024)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    st.subheader("Markiere die Objekte")
    canvas_result = st_canvas(
        background_image=img,
        height=img.height,
        width=img.width,
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        fill_color="",
        drawing_mode="circle",
        key="canvas"
    )

    # ---------------- Auswertung ----------------
    if canvas_result.json_data:
        objects = canvas_result.json_data["objects"]
        st.success(f"Markierte Objekte: {len(objects)}")

        # Punkte als CSV vorbereiten
        def points_to_csv(objects):
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["x","y","radius"])
            for obj in objects:
                x = obj["left"] + obj["radius"]
                y = obj["top"] + obj["radius"]
                r = obj["radius"]
                writer.writerow([x,y,r])
            return buf.getvalue().encode("utf-8")

        csv_bytes = points_to_csv(objects)
        st.download_button("📥 Markierte Punkte als CSV herunterladen", 
                           data=csv_bytes, file_name="marked_points.csv", mime="text/csv")
