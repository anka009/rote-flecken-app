import streamlit as st
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import base64
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Zellkern-Zähler", layout="wide")
st.title("🔬 Zellkern-Zähler mit Korrektur")

# -------- Hilfsfunktionen -------- #
def pil_to_base64(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    return "data:image/png;base64," + base64.b64encode(byte_im).decode()

def detect_cells_opencv(pil_image, min_radius=5, max_radius=50):
    img = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.medianBlur(gray, 5)

    params = cv2.SimpleBlobDetector_Params()
    params.filterByColor = False
    params.filterByArea = True
    params.minArea = np.pi * (min_radius ** 2)
    params.maxArea = np.pi * (max_radius ** 2)
    params.filterByCircularity = False
    params.filterByConvexity = False
    params.filterByInertia = False

    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(gray)

    points = [(int(k.pt[0]), int(k.pt[1])) for k in keypoints]

    img_marked = img.copy()
    for (x, y) in points:
        cv2.circle(img_marked, (x, y), 8, (0, 255, 0), 2)

    return points, Image.fromarray(img_marked)

# -------- Session State -------- #
if "detected_points" not in st.session_state:
    st.session_state.detected_points = []
if "added_points" not in st.session_state:
    st.session_state.added_points = []
if "removed_points" not in st.session_state:
    st.session_state.removed_points = []
if "uploaded_img" not in st.session_state:
    st.session_state.uploaded_img = None

# -------- Tabs -------- #
tab1, tab2 = st.tabs(["📊 Analyse", "✏️ Korrektur"])

with tab1:
    uploaded_file = st.file_uploader("Bild hochladen", type=["png", "jpg", "jpeg", "tif", "tiff"])
    min_r = st.slider("Minimaler Radius", 2, 50, 5)
    max_r = st.slider("Maximaler Radius", 10, 200, 50)

    if uploaded_file:
        pil_img = Image.open(uploaded_file)
        st.session_state.uploaded_img = pil_img

        detected_points, marked_img = detect_cells_opencv(pil_img, min_r, max_r)
        st.session_state.detected_points = detected_points

        st.image(marked_img, caption=f"Gefundene Zellkerne: {len(detected_points)}")
    else:
        st.info("Bitte ein Bild hochladen.")

with tab2:
    if st.session_state.uploaded_img is None:
        st.warning("Bitte zuerst ein Bild in 'Analyse' hochladen.")
    else:
        st.markdown("**Grün = hinzufügen, Rot = löschen**")

        # Hintergrundbild als Base64
        img_b64 = pil_to_base64(st.session_state.uploaded_img)

        # Canvas für Hinzufügen
        canvas_add = st_canvas(
            fill_color="rgba(0,255,0,0.6)",
            stroke_width=5,
            background_image=img_b64,
            update_streamlit=True,
            height=st.session_state.uploaded_img.height,
            width=st.session_state.uploaded_img.width,
            drawing_mode="point",
            key="canvas_add"
        )

        # Canvas für Löschen
        canvas_remove = st_canvas(
            fill_color="rgba(255,0,0,0.6)",
            stroke_width=5,
            background_image=img_b64,
            update_streamlit=True,
            height=st.session_state.uploaded_img.height,
            width=st.session_state.uploaded_img.width,
            drawing_mode="point",
            key="canvas_remove"
        )

        if st.button("Feedback speichern"):
            # Extrahiere neue Punkte aus Canvas-JSON
            if canvas_add.json_data is not None:
                added = [(int(obj["left"]), int(obj["top"])) for obj in canvas_add.json_data["objects"]]
                st.session_state.added_points.extend(added)

            if canvas_remove.json_data is not None:
                removed = [(int(obj["left"]), int(obj["top"])) for obj in canvas_remove.json_data["objects"]]
                st.session_state.removed_points.extend(removed)

            # Berechne neue Gesamtpunkte
            final_points = set(st.session_state.detected_points)
            final_points.update(st.session_state.added_points)
            final_points.difference_update(st.session_state.removed_points)

            # Markiertes Bild erstellen
            img_final = np.array(st.session_state.uploaded_img.convert("RGB"))
            for (x, y) in final_points:
                cv2.circle(img_final, (x, y), 8, (0, 255, 0), 2)

            st.image(img_final, caption=f"Korrigierte Zellkerne: {len(final_points)}")

