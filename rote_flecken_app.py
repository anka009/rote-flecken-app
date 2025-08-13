import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="Hybrid Bildanalyse", layout="wide")
st.title("🖌 Mensch & Maschine Team Workflow (OpenCV-Overlay)")

# ------------------------
# Bild-Upload
# ------------------------
uploaded_file = st.sidebar.file_uploader("Bild auswählen", type=["png","jpg","jpeg"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)
    height, width = img_np.shape[:2]

    # ------------------------
    # Transparenz einstellen
    # ------------------------
    st.sidebar.subheader("Overlay-Transparenz")
    alpha = st.sidebar.slider("Transparenz Überlagerung", 0.0, 1.0, 0.3)

    # ------------------------
    # Kreisparameter
    # ------------------------
    st.sidebar.subheader("Kreis-Parameter")
    radius_slider = st.sidebar.slider("Radius in Pixel", 5, 200, 20)
    radius_input = st.sidebar.number_input("Radius exakt eingeben", 1, 500, radius_slider)
    radius = radius_input

    # ------------------------
    # Zeichenmodus
    # ------------------------
    mode = st.sidebar.radio("Zeichenmodus", ("Punkt/Kreis", "Polygon"))

    drawing_mode = "point" if mode == "Punkt/Kreis" else "polygon"

    # ------------------------
    # Canvas zum Erfassen von Punkten/Polygonen
    # ------------------------
    canvas_result = st_canvas(
        fill_color=f"rgba(255,0,0,{alpha})",
        stroke_color=f"rgba(255,0,0,{alpha})",
        stroke_width=2,
        background_color="white",  # nur Hintergrund für Canvas-Feld, Bild wird später gezeichnet
        update_streamlit=True,
        height=height,
        width=width,
        drawing_mode=drawing_mode,
        key="canvas"
    )

    # ------------------------
    # Session State für Strukturen
    # ------------------------
    if "polygons" not in st.session_state:
        st.session_state.polygons = []
    if "circles" not in st.session_state:
        st.session_state.circles = []

    # ------------------------
    # Punkte/Polygone speichern
    # ------------------------
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        new_polygons = []
        new_circles = []
        for obj in objects:
            if obj["type"] == "polygon":
                points = [(p["x"], p["y"]) for p in obj["path"]]
                new_polygons.append(points)
            elif obj["type"] == "point":
                x = obj["left"]
                y = obj["top"]
                new_circles.append((x, y))
        if new_polygons != st.session_state.polygons:
            st.session_state.polygons = new_polygons
        if new_circles:
            st.session_state.circles.extend([c for c in new_circles if c not in st.session_state.circles])

    st.write(f"Anzahl Polygone: {len(st.session_state.polygons)}")
    st.write(f"Anzahl Kreise: {len(st.session_state.circles)}")

    # ------------------------
    # Overlay auf Bild zeichnen
    # ------------------------
    overlay = np.zeros_like(img_np, dtype=np.uint8)

    # Polygone
    for poly in st.session_state.polygons:
        pts = np.array(poly, np.int32).reshape((-1,1,2))
        cv2.fillPoly(overlay, [pts], (255,0,0))  # Rot

    # Kreise
    for x, y in st.session_state.circles:
        cv2.circle(overlay, (int(x), int(y)), int(radius), (0,255,0), -1)  # Grün

    # Überlagerung mit Transparenz kombinieren
    combined = cv2.addWeighted(img_np, 1.0, overlay, alpha, 0)
    st.image(combined, caption="Strukturen direkt auf Bild", use_column_width=True)
