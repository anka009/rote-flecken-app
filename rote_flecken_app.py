import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import io

st.set_page_config(page_title="Interaktiver Objekte-Zähler", layout="wide")
st.title("🖌️ Interaktiver Objekte-Zähler")

uploaded_file = st.file_uploader(
    "Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)",
    type=["png", "jpg", "jpeg", "tif", "tiff"]
)

if uploaded_file:
    # PIL Image öffnen, TIF/TIFF in RGB konvertieren
    pil = Image.open(uploaded_file)
    if pil.mode != "RGB":
        pil = pil.convert("RGB")

    # max Canvas Größe auf 800x800
    max_size = (800, 800)
    pil.thumbnail(max_size, Image.Resampling.LANCZOS)

    # PNG Bytes erzeugen
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    buf.seek(0)
    pil_for_canvas = Image.open(buf)

    st.sidebar.header("Einstellungen für Markierung")
    radius = st.sidebar.slider("Radius der Markierungen (px)", 5, 50, 15)
    color = st.sidebar.color_picker("Farbe der Markierung", "#00FF00")
    thickness = st.sidebar.slider("Linienstärke", 1, 10, 2)

    st.subheader("Markiere die Objekte")
    canvas_result = st_canvas(
        fill_color="",
        stroke_width=thickness,
        stroke_color=color,
        background_image=pil_for_canvas,
        update_streamlit=True,
        height=pil_for_canvas.height,
        width=pil_for_canvas.width,
        drawing_mode="circle",
        key="canvas"
    )

    count = 0
    if canvas_result.json_data:
        objects = canvas_result.json_data["objects"]
        count = len(objects)

    st.markdown(f"### Anzahl markierter Objekte: **{count}**")
