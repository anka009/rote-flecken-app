import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="Hybrid Bildanalyse", layout="wide")
st.title("🖌 Mensch & Maschine Team Workflow (Kreise + Polygon)")

# ------------------------
# Bild-Upload
# ------------------------
uploaded_file = st.sidebar.file_uploader("Bild auswählen", type=["png","jpg","jpeg"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)
    st.image(img, caption="Originalbild", use_column_width=True)

    # ------------------------
    # Radius-Einstellungen für Kreise
    # ------------------------
    st.sidebar.subheader("Kreis-Parameter")
    radius = st.sidebar.slider("Radius in Pixel", min_value=5, max_value=200, value=20)
    radius_input = st.sidebar.number_input("Radius exakt eingeben", min_value=1, max_value=500, value=radius)
    radius = radius_input  # überschreibt Slider, falls Zahl eingegeben

    # ------------------------
    # Canvas-Einstellungen
    # ------------------------
    canvas_result = st_canvas(
        fill_color="rgba(255,0,0,0.3)",
        stroke_color="red",
        stroke_width=2,
        background_color="white",  # Canvas selbst sichtbar
        update_streamlit=True,
        height=img_np.shape[0],
        width=img_np.shape[1],
        drawing_mode="point",  # Klickpunkte für Kreismittel
        key="canvas"
    )

    # ------------------------
    # Session State für Kreise
    # ------------------------
    if "circles" not in st.session_state:
        st.session_state.circles = []

    # Punkte aus Canvas speichern
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        for obj in objects:
            if obj["type"] == "circle" or obj["type"] == "point":
                x = obj["left"]
                y = obj["top"]
                # Prüfen, ob Punkt schon existiert
                if (x,y) not in st.session_state.circles:
                    st.session_state.circles.append((x,y))

    st.write(f"Anzahl markierter Strukturen (Kreise): {len(st.session_state.circles)}")

    # ------------------------
    # Maske erzeugen
    # ------------------------
    if st.button("Maske aus Kreisen erzeugen"):
        mask = np.zeros((img_np.shape[0], img_np.shape[1]), dtype=np.uint8)
        for x, y in st.session_state.circles:
            cv2.circle(mask, (int(x), int(y)), int(radius), 255, -1)  # gefüllter Kreis
        st.image(mask, caption="Maske der Kreise", use_column_width=True)
        st.success("Maske erzeugt, Kreise gezählt!")
