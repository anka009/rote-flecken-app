import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="Hybrid Bildanalyse", layout="wide")
st.title("🖌 Mensch & Maschine Team Workflow (Direkt auf Bild)")

# ------------------------
# Bild-Upload
# ------------------------
uploaded_file = st.sidebar.file_uploader("Bild auswählen", type=["png","jpg","jpeg"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)
    st.sidebar.subheader("Canvas-Transparenz")
    alpha = st.sidebar.slider("Transparenz Canvas", 0.0, 1.0, 0.2)

    # ------------------------
    # Kreisparameter
    # ------------------------
    st.sidebar.subheader("Kreis-Parameter")
    radius_slider = st.sidebar.slider("Radius in Pixel", min_value=5, max_value=200, value=20)
    radius_input = st.sidebar.number_input("Radius exakt eingeben", min_value=1, max_value=500, value=radius_slider)
    radius = radius_input

    # ------------------------
    # Zeichenmodus
    # ------------------------
    mode = st.sidebar.radio("Zeichenmodus", ("Punkt/Kreis", "Polygon"))
    drawing_mode = "point" if mode=="Punkt/Kreis" else "polygon"

    # ------------------------
    # Canvas direkt über das Bild
    # ------------------------
    canvas_result = st_canvas(
        fill_color=f"rgba(255,0,0,{alpha})",
        stroke_color=f"rgba(255,0,0,{alpha})",
        stroke_width=2,
        background_color=None,  # kein separates Feld
        update_streamlit=True,
        height=img_np.shape[0],
        width=img_np.shape[1],
        drawing_mode=drawing_mode,
        key="canvas"
    )

    # ------------------------
    # Session State
    # ------------------------
    if "polygons" not in st.session_state:
        st.session_state.polygons = []
    if "circles" not in st.session_state:
        st.session_state.circles = []

    # ------------------------
    # Polygone + Punkte speichern
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
                new_circles.append((x,y))
        if new_polygons != st.session_state.polygons:
            st.session_state.polygons = new_polygons
        if new_circles:
            st.session_state.circles.extend([c for c in new_circles if c not in st.session_state.circles])

    st.write(f"Anzahl Polygone: {len(st.session_state.polygons)}")
    st.write(f"Anzahl Kreise: {len(st.session_state.circles)}")

    # ------------------------
    # Maske erzeugen
    # ------------------------
    if st.button("Maske erzeugen"):
        mask = img_np.copy()  # Bild kopieren
        overlay = np.zeros_like(mask, dtype=np.uint8)

        # Polygone
        for poly in st.session_state.polygons:
            pts = np.array(poly, np.int32).reshape((-1,1,2))
            cv2.fillPoly(overlay, [pts], (255,255,255))

        # Kreise
        for x, y in st.session_state.circles:
            cv2.circle(overlay, (int(x), int(y)), int(radius), (255,255,255), -1)

        # Transparenz kombinieren
        combined = cv2.addWeighted(mask, 1.0, overlay, alpha, 0)
        st.image(combined, caption="Strukturen direkt auf Bild", use_column_width=True)
        st.success("Maske erzeugt, alle Strukturen sichtbar!")
