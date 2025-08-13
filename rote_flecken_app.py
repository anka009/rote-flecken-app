import streamlit as st
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="Hybrid Bildanalyse", layout="wide")
st.title("🖌 Marker direkt auf Bild (OpenCV)")

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

    # ------------------------
    # Session State
    # ------------------------
    if "points" not in st.session_state:
        st.session_state.points = []  # für Kreise
    if "current_polygon" not in st.session_state:
        st.session_state.current_polygon = []  # Polygon in Bearbeitung
    if "polygons" not in st.session_state:
        st.session_state.polygons = []  # fertige Polygone

    # ------------------------
    # Kreise setzen
    # ------------------------
    st.subheader("Kreise setzen")
    col1, col2 = st.columns(2)
    with col1:
        x = st.number_input("X-Koordinate", min_value=0, max_value=width-1, value=width//2)
        y = st.number_input("Y-Koordinate", min_value=0, max_value=height-1, value=height//2)
        if st.button("Kreis hinzufügen"):
            st.session_state.points.append((x,y))

    # ------------------------
    # Polygon zeichnen
    # ------------------------
    with col2:
        st.write("Polygon-Modus")
        px = st.number_input("Polygon X", min_value=0, max_value=width-1, value=width//2, key="px")
        py = st.number_input("Polygon Y", min_value=0, max_value=height-1, value=height//2, key="py")
        if st.button("Punkt zum Polygon"):
            st.session_state.current_polygon.append((px,py))
        if st.button("Polygon fertig"):
            if st.session_state.current_polygon:
                st.session_state.polygons.append(st.session_state.current_polygon.copy())
                st.session_state.current_polygon = []

    # ------------------------
    # Overlay auf Bild
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

    # aktuelles Polygon (in Bearbeitung)
    if st.session_state.current_polygon:
        pts = np.array(st.session_state.current_polygon, np.int32).reshape((-1,1,2))
        cv2.polylines(overlay, [pts], isClosed=False, color=(0,0,255), thickness=2)

    st.image(overlay, caption="Marker direkt auf Bild", use_column_width=True)
    st.write(f"Anzahl Kreise: {len(st.session_state.points)}")
    st.write(f"Anzahl Polygone: {len(st.session_state.polygons)}")
