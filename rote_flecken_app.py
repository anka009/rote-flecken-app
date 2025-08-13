import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import cv2
import io
import csv

st.set_page_config(page_title="🖌️ Interaktiver Objekte-Zähler", layout="wide")
st.title("🖌️ Interaktiver Objekte-Zähler")

# ---------------- Einstellungen Sidebar ----------------
st.sidebar.header("Einstellungen für Markierung")
radius = st.sidebar.slider("Radius der Markierungen (px)", 1, 50, 10)
color = st.sidebar.color_picker("Farbe der Markierung", "#ff0000")
line_width = st.sidebar.slider("Linienstärke", 1, 10, 2)

# ---------------- Bild Upload ----------------
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if uploaded_file:
    # Bild öffnen
    img = Image.open(uploaded_file)

    # Bei TIFF automatisch konvertieren
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Bild skalieren, max 800x800 für Canvas
    max_size = (800, 800)
    img.thumbnail(max_size, Image.ANTIALIAS)
    
    img_np = np.array(img)

    # ---------------- Canvas ----------------
    st.subheader("Markiere die Objekte")
    canvas_result = st_canvas(
        fill_color="",  # keine Füllung
        stroke_width=line_width,
        stroke_color=color,
        background_image=img,
        update_streamlit=True,
        height=img.height,
        width=img.width,
        drawing_mode="circle",
        key="canvas"
    )

    # ---------------- Punkte extrahieren ----------------
    points = []
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        for obj in objects:
            if obj["type"] == "circle":
                x = obj["left"] + obj["radius"]
                y = obj["top"] + obj["radius"]
                r = obj["radius"]
                points.append((x, y, r))

    # ---------------- Live-Zählung ----------------
    st.markdown(f"**Anzahl markierter Objekte:** {len(points)}")

    # ---------------- CSV Export ----------------
    if points:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["x","y","radius"])
        for p in points:
            writer.writerow([int(p[0]), int(p[1]), int(p[2])])
        st.download_button("📥 CSV der markierten Objekte herunterladen", data=buf.getvalue(), file_name="markierte_objekte.csv", mime="text/csv")
