import streamlit as st
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="Interaktive Marker", layout="wide")
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
    radius = st.sidebar.slider("Kreis-Radius in Pixel", 5, 100, 20)
    circle_color = (0,255,0)  # Grün
    poly_color = (255,0,0)    # Rot

    # ------------------------
    # Session State
    # ------------------------
    if "circles" not in st.session_state:
        st.session_state.circles = []  # (x, y)
    if "polygons" not in st.session_state:
        st.session_state.polygons = []  # Liste von Polygonen
    if "current_poly" not in st.session_state:
        st.session_state.current_poly = []

    # ------------------------
    # Kreise per Klick hinzufügen
    # ------------------------
    st.subheader("Kreise setzen durch Klicken")
    clicked_x = st.number_input("X-Koordinate", min_value=0, max_value=width-1, value=width//2)
    clicked_y = st.number_input("Y-Koordinate", min_value=0, max_value=height-1, value=height//2)
    if st.button("Kreis hinzufügen"):
        st.session_state.circles.append((clicked_x, clicked_y))

    # ------------------------
    # Polygon-Modus
    # ------------------------
    st.subheader("Polygon-Modus")
    px = st.number_input("Polygon X", min_value=0, max_value=width-1, value=width//2, key="px")
    py = st.number_input("Polygon Y", min_value=0, max_value=height-1, value=height//2, key="py")
    if st.button("Punkt zum Polygon"):
        st.session_state.current_poly.append((px, py))
    if st.button("Polygon fertig"):
        if st.session_state.current_poly:
            st.session_state.polygons.append(st.session_state.current_poly.copy())
            st.session_state.current_poly = []

    # ------------------------
    # Overlay auf Bild
    # ------------------------
    overlay = img_np.copy()

    # Kreise als Outline
    for x, y in st.session_state.circles:
        cv2.circle(overlay, (int(x), int(y)), radius, circle_color, thickness=2)  # Outline

    # Polygone
    for poly in st.session_state.polygons:
        pts = np.array(poly, np.int32).reshape((-1,1,2))
        cv2.polylines(overlay, [pts], isClosed=True, color=poly_color, thickness=2)

    # aktuelles Polygon (in Bearbeitung)
    if st.session_state.current_poly:
        pts = np.array(st.session_state.current_poly, np.int32).reshape((-1,1,2))
        cv2.polylines(overlay, [pts], isClosed=False, color=(0,0,255), thickness=2)

    st.image(overlay, caption="Marker direkt auf Bild", use_column_width=True)
    st.write(f"Anzahl Kreise: {len(st.session_state.circles)}")
    st.write(f"Anzahl Polygone: {len(st.session_state.polygons)}")
