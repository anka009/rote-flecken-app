import streamlit as st
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas
import io

st.set_page_config(page_title="🖌️ Interaktiver Objekte-Zähler", layout="wide")
st.title("🖌️ Interaktiver Objekte-Zähler — Stufe 3.1")

st.sidebar.header("Einstellungen für Markierung")
radius = st.sidebar.slider("Radius der Markierungen (px)", 1, 50, 10)
color = st.sidebar.color_picker("Farbe der Markierung", "#FF0000")
line_width = st.sidebar.slider("Linienstärke", 1, 10, 2)

uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if uploaded_file:
    # PIL-Image laden
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)

    # Hintergrundbild als Bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.markdown("**Markiere die Objekte direkt im Bild**")
    canvas_result = st_canvas(
        fill_color="",
        stroke_width=line_width,
        stroke_color=color,
        background_image=Image.open(io.BytesIO(byte_im)),
        update_streamlit=True,
        height=img.height,
        width=img.width,
        drawing_mode="circle",
        key="canvas"
    )

    # Punkte auslesen
    points = []
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        for obj in objects:
            if obj["type"] == "circle":
                x = int(obj["left"] + obj["radius"])
                y = int(obj["top"] + obj["radius"])
                r = int(obj["radius"])
                points.append((x, y, r))

    st.write(f"Gefundene / markierte Objekte: **{len(points)}**")
