import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="Hybrid Bildanalyse", layout="wide")
st.title("🖌 Interaktive Kreise & Polygone direkt auf Bild")

# ------------------------
# Bild-Upload
# ------------------------
uploaded_file = st.sidebar.file_uploader("Bild auswählen", type=["png","jpg","jpeg"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)
    height, width = img_np.shape[:2]

    # ------------------------
    # Kreisparameter
    # ------------------------
    st.sidebar.subheader("Kreis-Parameter")
    radius = st.sidebar.slider("Radius in Pixel", 5, 200, 20)

    # ------------------------
    # Zeichenmodus
    # ------------------------
    mode = st.sidebar.radio("Zeichenmodus", ("Kreis setzen", "Polygon zeichnen"))
    drawing_mode = "point" if mode=="Kreis setzen" else "polygon"

    # ------------------------
    # Session State
    # ------------------------
    if "points" not in st.session_state:
        st.session_state.points = []  # für Kreise
    if "polygons" not in st.session_state:
        st.session_state.polygons = []  # Liste von Polygonen

    # ------------------------
    # Canvas zum Erfassen von Klicks
    # ------------------------
    canvas_result = st_canvas(
        fill_color=f"rgba(0,255,0,0.3)",
        stroke_color=f"rgba(255,0,0,0.6)",
        stroke_width=2,
        background_color=None,  # transparent, Bild separat
        update_streamlit=True,
        height=height,
        width=width,
        drawing_mode=drawing_mode,
        key="canvas"
    )

    # ------------------------
    # Objekte aus Canvas auslesen
    # ------------------------
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        new_points = []
        new_polygons = []
        for obj in objects:
            if obj["type"] == "point":
                x, y = obj["left"], obj["top"]
                if (x,y) not in st.session_state.points:
                    new_points.append((x,y))
            elif obj["type"] == "polygon":
                pts = [(p["x"], p["y"]) for p in obj["path"]]
                if pts not in st.session_state.polygons:
                    new_polygons.append(pts)
        st.session_state.points.extend(new_points)
        st.session_state.polygons.extend(new_polygons)

    # ------------------------
    # Overlay auf Bild zeichnen
    # ------------------------
    overlay = img_np.copy()

    # Kreise
    for x, y in st.session_state.points:
        cv2.circle(overlay, (int(x), int(y)), radius, (0,255,0), -1)

    # Polygone
    for poly in st.session_state.polygons:
        pts = np.array(poly, np.int32).reshape((-1,1,2))
        cv2.polylines(overlay, [pts], isClosed=True, color=(255,0,0), thickness=2)
        cv2.fillPoly(overlay, [pts], (255,0,0,50))  # leicht transparent

    st.image(overlay, caption="Interaktive Marker direkt auf Bild", use_column_width=True)
    st.write(f"Anzahl Kreise: {len(st.session_state.points)}")
    st.write(f"Anzahl Polygone: {len(st.session_state.polygons)}")
