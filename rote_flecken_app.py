import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
from skimage.draw import polygon2mask

st.set_page_config(page_title="Hybrid Bildanalyse", layout="wide")
st.title("🖌 Mensch & Maschine Team Workflow")

# ------------------------
# Bild-Upload
# ------------------------
uploaded_file = st.sidebar.file_uploader("📁 Bild auswählen", type=["png", "jpg", "jpeg"])
if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Originalbild", use_column_width=True)

    # ------------------------
    # Canvas-Einstellungen
    # ------------------------
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",  # halbtransparent rot
        stroke_color="red",
        stroke_width=2,
        background_image=img,
        update_streamlit=True,
        height=img.height,
        width=img.width,
        drawing_mode="polygon",
        key="canvas",
    )

    # ------------------------
    # Punkte/Polygone speichern
    # ------------------------
    if "polygons" not in st.session_state:
        st.session_state.polygons = []

    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        # Neue Polygone extrahieren
        new_polygons = []
        for obj in objects:
            if obj["type"] == "polygon":
                points = [(p["x"], p["y"]) for p in obj["path"]]
                new_polygons.append(points)

        # Alle neuen Polygone abspeichern, nur wenn es neue gibt
        if new_polygons and new_polygons != st.session_state.polygons:
            st.session_state.polygons = new_polygons

    st.write(f"Anzahl markierter Strukturen: {len(st.session_state.polygons)}")

    # ------------------------
    # Maske aus Polygonen erzeugen
    # ------------------------
    if st.button("Maschine analysiert markierte Strukturen"):
        img_np = np.array(img)
        mask = np.zeros(img_np.shape[:2], dtype=bool)

        for poly in st.session_state.polygons:
            poly_mask = polygon2mask(img_np.shape[:2], poly)
            mask = mask | poly_mask

        st.image(mask.astype(np.uint8)*255, caption="Maske der markierten Strukturen", use_column_width=True)
        st.success("Maschine kann nun ähnliche Strukturen im Bild suchen!")

