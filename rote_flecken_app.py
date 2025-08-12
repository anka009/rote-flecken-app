import streamlit as st
import cv2
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- Hilfsfunktion: Immer PIL-Image erzeugen ---
def to_pil(img):
    if img is None:
        return None
    if isinstance(img, np.ndarray):
        return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    if isinstance(img, Image.Image):
        return img
    raise TypeError("background_image muss PIL.Image oder NumPy sein")

# --- Blob Detection ---
def detect_blobs(img, min_radius=5, max_radius=50):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)

    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = np.pi * (min_radius ** 2)
    params.maxArea = np.pi * (max_radius ** 2)
    params.filterByCircularity = False
    params.filterByConvexity = False
    params.filterByInertia = False

    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(gray)

    img_marked = cv2.drawKeypoints(img, keypoints, np.array([]),
                                   (0, 0, 255),
                                   cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    centers = [(int(k.pt[0]), int(k.pt[1])) for k in keypoints]
    return img_marked, centers

# --- Streamlit Layout ---
st.set_page_config(page_title="Zellkern-Analyse", layout="wide")
st.title("🔬 Zellkern-Analyse & Interaktive Korrektur")

tab1, tab2 = st.tabs(["Analyse", "Korrektur"])

# --- Tab 1: Analyse ---
with tab1:
    uploaded_file = st.file_uploader("Bild hochladen", type=["png", "jpg", "jpeg", "tif", "tiff"])

    if uploaded_file:
        pil_image = Image.open(uploaded_file).convert("RGB")
        opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        min_r = st.slider("Min Radius (Pixel)", 1, 50, 5)
        max_r = st.slider("Max Radius (Pixel)", 10, 200, 50)

        marked_img, detected_points = detect_blobs(opencv_image, min_r, max_r)
        st.image(cv2.cvtColor(marked_img, cv2.COLOR_BGR2RGB), caption=f"Gefundene Zellkerne: {len(detected_points)}")
        st.session_state["analysis_image"] = pil_image
        st.session_state["detected_points"] = detected_points
    else:
        st.info("Bitte zuerst ein Bild hochladen.")

# --- Tab 2: Korrektur ---
with tab2:
    if "analysis_image" in st.session_state:
        base_img = to_pil(st.session_state["analysis_image"])

        st.markdown("### ✏️ Interaktive Korrektur — oben **GRÜN** = hinzufügen, unten **ROT** = löschen")

        # --- Punkte hinzufügen (Grün) ---
        canvas_add = st_canvas(
            fill_color="rgba(0,255,0,0.6)",
            stroke_width=10,
            background_image=base_img,
            height=base_img.height,
            width=base_img.width,
            drawing_mode="point",
            key="canvas_add"
        )

        # --- Punkte löschen (Rot) ---
        canvas_remove = st_canvas(
            fill_color="rgba(255,0,0,0.6)",
            stroke_width=10,
            background_image=base_img,
            height=base_img.height,
            width=base_img.width,
            drawing_mode="point",
            key="canvas_remove"
        )

        if st.button("Feedback speichern"):
            add_points = canvas_add.json_data["objects"] if canvas_add.json_data else []
            remove_points = canvas_remove.json_data["objects"] if canvas_remove.json_data else []
            st.success(f"Hinzugefügt: {len(add_points)} | Entfernt: {len(remove_points)}")
    else:
        st.warning("Bitte zuerst im Tab 'Analyse' ein Bild hochladen und analysieren.")

