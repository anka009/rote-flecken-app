import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="Hybrid Bildanalyse", layout="wide")
st.title("🖌 Mensch & Maschine Team Workflow")

# ------------------------
# Bild-Upload
# ------------------------
uploaded_file = st.sidebar.file_uploader("📁 Bild auswählen", type=["png", "jpg", "jpeg"])
if uploaded_file:
    # Bild stabil laden & in RGB konvertieren
    img = Image.open(uploaded_file).convert("RGB")
    st.image(img, caption="Originalbild", use_column_width=True)

    # ------------------------
    # Canvas-Einstellungen (ohne Hintergrund)
    # ------------------------
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",  # halbtransparent rot
        stroke_color="red",
        stroke_width=2,
        background_color="white",  # Canvas selbst ist sichtbar, Hintergrundbild entfällt
        update_streamlit=True,
        height=img.height,
        width=img.width,
        drawing_mode="polygon",
        key="canvas",
    )

    # ------------------------
    # Polygone speichern
    # ------------------------
    if "polygons" not in st.session_state:
        st.session_state.polygons = []

    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        new_polygons = []
        for obj in objects:
            if obj["type"] == "polygon":
                points = [(p["x"], p["y"]) for p in obj["path"]]
                new_polygons.append(points)
        
        if new_polygons != st.session_state.polygons:
            st.session_state.polygons = new_polygons

    st.write(f"Anzahl markierter Strukturen: {len(st.session_state.polygons)}")

    # ------------------------
    # Maske aus Polygonen erzeugen (OpenCV)
    # ------------------------
    if st.button("Maschine analysiert markierte Strukturen"):
        mask = np.zeros((img.height, img.width), dtype=np.uint8)
        for poly in st.session_state.polygons:
            pts = np.array(poly, np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(mask, [pts], 255)
        st.image(mask, caption="Maske der markierten Strukturen", use_column_width=True)
        st.success("Maschine kann nun ähnliche Strukturen im Bild suchen!")
