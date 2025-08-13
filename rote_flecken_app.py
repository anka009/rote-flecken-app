import streamlit as st
from PIL import Image
import numpy as np
import cv2

try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAVE_CLICK = True
except:
    HAVE_CLICK = False

st.set_page_config(page_title="🖌️ Interaktive Korrektur im Bild", layout="wide")
st.title("🖌️ Korrektur direkt im Bild")

# Upload
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    max_size = (1024, 1024)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    if "points" not in st.session_state:
        st.session_state["points"] = []

    radius = st.sidebar.slider("Radius der Markierungen", 1, 50, 10)
    line_thickness = st.sidebar.slider("Linienstärke", 1, 10, 2)
    color_picker = st.sidebar.color_picker("Farbe der Markierung", "#ff0000")

    rgb_color = tuple(int(color_picker.lstrip("#")[i:i+2], 16) for i in (0,2,4))
    bgr_color = rgb_color[::-1]

    st.write("Klicke auf bestehenden Punkt zum Löschen oder auf leeren Bereich zum Hinzufügen.")

    # Klick erfassen
    if HAVE_CLICK:
        coords = streamlit_image_coordinates(img, key="coords")
        if coords:
            x, y = coords["x"], coords["y"]
            removed = False
            for i, (px, py) in enumerate(st.session_state["points"]):
                if (px - x)**2 + (py - y)**2 <= radius**2:
                    st.session_state["points"].pop(i)
                    removed = True
                    break
            if not removed:
                st.session_state["points"].append((x, y))

    # Bild mit Punkten
    img_array = np.array(img)
    marked = img_array.copy()
    for (x, y) in st.session_state["points"]:
        cv2.circle(marked, (x, y), radius, bgr_color, line_thickness)

    # Zähler direkt ins Bild zeichnen
    cv2.putText(marked, f"Objekte: {len(st.session_state['points'])}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

    st.image(marked, use_column_width=True)
