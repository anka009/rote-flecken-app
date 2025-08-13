import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# ----------------------------------------
# Hilfsfunktionen
# ----------------------------------------
def load_image(file):
    img = Image.open(file)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.array(img)

def detect_blobs(image, min_radius=5, max_radius=50):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    # Blob-Parameter
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = np.pi * (min_radius ** 2)
    params.maxArea = np.pi * (max_radius ** 2)
    params.filterByCircularity = False
    params.filterByInertia = False
    params.filterByConvexity = False

    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(gray)
    coords = [(int(k.pt[0]), int(k.pt[1])) for k in keypoints]
    return coords

def draw_points(image, points, color=(0, 255, 0)):
    img_copy = image.copy()
    for (x, y) in points:
        cv2.circle(img_copy, (x, y), 5, color, -1)
    return img_copy

# ----------------------------------------
# Session State initialisieren
# ----------------------------------------
if "added_points" not in st.session_state:
    st.session_state.added_points = []
if "removed_points" not in st.session_state:
    st.session_state.removed_points = []
if "detected_points" not in st.session_state:
    st.session_state.detected_points = []

# ----------------------------------------
# UI
# ----------------------------------------
st.set_page_config(layout="wide")
tab1, tab2 = st.tabs(["🔍 Analyse", "✏️ Korrektur"])

with tab1:
    st.header("Analyse")
    uploaded_file = st.file_uploader(
        "Bild hochladen",
        type=["png", "jpg", "jpeg", "tif", "tiff"]
    )
    min_radius = st.slider("Minimaler Radius", 1, 50, 5)
    max_radius = st.slider("Maximaler Radius", 10, 200, 50)

    if uploaded_file:
        image = load_image(uploaded_file)
        coords = detect_blobs(image, min_radius, max_radius)
        st.session_state.detected_points = coords

        result_img = draw_points(image, coords, (0, 255, 0))

        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="Original", use_container_width=True)
        with col2:
            st.image(result_img, caption=f"Gefundene Strukturen: {len(coords)}", use_container_width=True)

with tab2:
    st.header("Manuelle Korrektur")

    if len(st.session_state.detected_points) == 0:
        st.warning("Bitte zuerst ein Bild im Analyse-Tab hochladen und analysieren.")
    else:
        st.write("Klicke ins Bild, um Punkte **hinzuzufügen** oder **zu entfernen**.")
        mode = st.radio("Modus", ["Hinzufügen", "Entfernen"], horizontal=True)

        # Klick-Koordinaten per Streamlit-Events
        click_x = st.number_input("X-Koordinate", min_value=0, value=0)
        click_y = st.number_input("Y-Koordinate", min_value=0, value=0)
        if st.button("Punkt hinzufügen/entfernen"):
            if mode == "Hinzufügen":
                st.session_state.added_points.append((click_x, click_y))
            else:
                st.session_state.removed_points.append((click_x, click_y))

        # Punkte anwenden
        current_points = [
            p for p in st.session_state.detected_points
            if p not in st.session_state.removed_points
        ] + st.session_state.added_points

        # Rückmeldung
        corrected_img = draw_points(
            load_image(uploaded_file),
            current_points,
            (0, 0, 255)
        )

        col1, col2 = st.columns(2)
        with col1:
            st.image(corrected_img, caption="Korrigiertes Bild", use_container_width=True)
        with col2:
            st.write("**Markierte Strukturen (Koordinaten):**")
            st.write(current_points)
            st.write(f"**Gesamtanzahl:** {len(current_points)}")

        if st.button("Feedback speichern"):
            # Speichern in Datei
            img_pil = Image.fromarray(corrected_img)
            buf = io.BytesIO()
            img_pil.save(buf, format="PNG")
            byte_im = buf.getvalue()
            st.download_button(
                label="Korrigiertes Bild herunterladen",
                data=byte_im,
                file_name="korrektur.png",
                mime="image/png"
            )
