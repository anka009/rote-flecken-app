import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageSequence
from streamlit_drawable_canvas import st_canvas

# 📥 Upload-Abschnitt
uploaded_files = st.file_uploader(
    "📁 Lade mehrere Bilder hoch",
    type=["jpg", "jpeg", "png", "tif", "tiff"],
    accept_multiple_files=True
)

# 📏 DPI und Umrechnung
dpi = 300
pixels_per_mm = dpi / 25.4

if uploaded_files:
    total_flecken = 0
    total_pixel_area = 0

    for uploaded_file in uploaded_files:
        st.header(f"🖼️ Datei: `{uploaded_file.name}`")

        try:
            image_pil = Image.open(uploaded_file)
            frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(image_pil)]
        except:
            try:
                image_single = Image.open(uploaded_file).convert("RGB")
                frames = [image_single]
            except:
                frames = []

        if not frames:
            st.error("❌ Bild konnte nicht verarbeitet werden.")
            continue

        for i, frame in enumerate(frames):
            if len(frames) > 1:
                st.subheader(f"📄 Seite {i+1}")

            image_np = np.array(frame)
            hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

            # 🎨 Farbdefinition
            lower_red1 = np.array([0, 70, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 70, 50])
            upper_red2 = np.array([180, 255, 255])
            lower_brown = np.array([10, 100, 20])
            upper_brown = np.array([30, 255, 200])

            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask3 = cv2.inRange(hsv, lower_brown, upper_brown)
            mask = cv2.bitwise_or(cv2.bitwise_or(mask1, mask2), mask3)

            kernel = np.ones((5, 5), np.uint8)
            mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            min_area = 50
            filtered = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
            def is_near(point, contour, threshold=20):
                px, py = point["left"], point["top"]
                for pt in contour:
                    x, y = pt[0]
                    if np.hypot(px - x, py - y) < threshold:
                        return True
                return False

            # 🖍️ Manuelle Bearbeitung
            st.markdown("### ➕ Flecken hinzufügen")
            canvas_add = st_canvas(
                fill_color="rgba(0, 255, 0, 0.3)",
                stroke_width=3,
                background_image=frame,
                update_streamlit=True,
                height=frame.height,
                width=frame.width,
                drawing_mode="point",
                key=f"add_{i}"
            )

            st.markdown("### ➖ Flecken löschen")
            canvas_del = st_canvas(
                fill_color="rgba(255, 0, 0, 0.3)",
                stroke_width=3,
                background_image=frame,
                update_streamlit=True,
                height=frame.height,
                width=frame.width,
                drawing_mode="point",
                key=f"del_{i}"
            )

            # 📌 Punkte auslesen
            add_points = canvas_add.json_data.get("objects", []) if canvas_add.json_data else []
            del_points = canvas_del.json_data.get("objects", []) if canvas_del.json_data else []

            # 🧠 Konturen löschen, wenn nahe an Löschpunkten
            def is_near(point, contour, threshold=20):
                px, py = point["left"], point["top"]
                for pt in contour:
                    x, y = pt[0]
                    if np.hypot(px -
