import streamlit as st
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
    height, width = img_np.shape[:2]

    # ------------------------
    # Kreisparameter
    # ------------------------
    st.sidebar.subheader("Kreis-Parameter")
    radius = st.sidebar.slider("Radius in Pixel", 5, 200, 20)

    # ------------------------
    # Zeichenmodus
    # ------------------------
    mode = st.sidebar.radio("Zeichenmodus", ("Punkt/Kreis", "Polygon"))

    # ------------------------
    # Session State
    # ------------------------
    if "points" not in st.session_state:
        st.session_state.points = []  # für Kreise
    if "polygons" not in st.session_state:
        st.session_state.polygons = []  # für Polygone

    # ------------------------
    # Eingabe-Klicks erfassen
    # ------------------------
    st.subheader("Bild-Klicks erfassen (x,y)")
    col1, col2 = st.columns(2)
    with col1:
        x = st.number_input("X-Koordinate", min_value=0, max_value=width-1, value=width//2)
        y = st.number_input("Y-Koordinate", min_value=0, max_value=height-1, value=height//2)
        if st.button("Kreis setzen"):
            st.session_state.points.append((x,y))
    with col2:
        st.write("Polygone manuell eingeben (nur Demo, später interaktiv möglich)")

    # ------------------------
    # Overlay erzeugen
    # ------------------------
    overlay = img_np.copy()

    # Kreise
    for px, py in st.session_state.points:
        cv2.circle(overlay, (int(px), int(py)), radius, (0,255,0), -1)  # gefüllt Grün

    # Polygone
    for poly in st.session_state.polygons:
        pts = np.array(poly, np.int32).reshape((-1,1,2))
        cv2.polylines(overlay, [pts], isClosed=True, color=(255,0,0), thickness=2)

    st.image(overlay, caption="Marker direkt auf Bild", use_column_width=True)
    st.write(f"Anzahl Kreise: {len(st.session_state.points)}")
    st.write(f"Anzahl Polygone: {len(st.session_state.polygons)}")
