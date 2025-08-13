import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import io
import csv

st.set_page_config(page_title="🖌️ Interaktiver Objekte-Zähler", layout="wide")
st.title("🖌️ Interaktiver Objekte-Zähler (Stufe 3.0)")

# -------------------- Upload --------------------
uploaded_file = st.file_uploader(
    "Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)",
    type=["png", "jpg", "jpeg", "tif", "tiff"]
)

if uploaded_file:
    # TIFF / TIF in RGB konvertieren
    pil_image = Image.open(uploaded_file)
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    img_width, img_height = pil_image.size

    # -------------------- Sidebar: Einstellungen --------------------
    st.sidebar.header("Einstellungen für Markierung")
    mark_radius = st.sidebar.slider("Radius der Markierungen (px)", 1, 50, 10)
    mark_color = st.sidebar.color_picker("Farbe der Markierung", "#ff0000")
    line_width = st.sidebar.slider("Linienstärke", 1, 10, 2)

    # Convert color hex to BGR tuple for OpenCV compatibility
    color_rgb = tuple(int(mark_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

    # -------------------- Canvas --------------------
    st.markdown("**Markiere die Objekte direkt im Bild**")
    canvas_result = st_canvas(
        fill_color="",  # Keine Füllung
        stroke_width=line_width,
        stroke_color=mark_color,
        background_image=pil_image,
        update_streamlit=True,
        height=img_height,
        width=img_width,
        drawing_mode="circle",
        key="canvas",
    )

    # -------------------- Punkte erfassen --------------------
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        points = []
        for obj in objects:
            # x,y sind der Mittelpunkt des Kreises
            left = obj["left"]
            top = obj["top"]
            radius = obj["radius"] if "radius" in obj else mark_radius
            x = int(left + radius)
            y = int(top + radius)
            points.append((x, y, radius))

        st.write(f"Gefundene Objekte: **{len(points)}**")

        # -------------------- CSV Export --------------------
        if points:
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["x", "y", "radius"])
            for p in points:
                writer.writerow(p)
            st.download_button(
                "📥 Markierte Punkte als CSV exportieren",
                data=buf.getvalue().encode("utf-8"),
                file_name="marked_points.csv",
                mime="text/csv",
            )
