import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageSequence

st.title("🔴 Rote Flecken Zähler")

uploaded_files = st.file_uploader("Lade mehrere Bilder hoch", type=["jpg", "jpeg", "png", "tif", "tiff"], accept_multiple_files=True)
from PIL import Image, ImageSequence

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.markdown(f"### 📷 Bild: `{uploaded_file.name}`")
        try:
            image_pil = Image.open(uploaded_file)
            frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(image_pil)]
        except:
            frames = [Image.open(uploaded_file).convert("RGB")]

        for i, frame in enumerate(frames):
            if len(frames) > 1:
                st.markdown(f"**🗂️ Seite {i+1}**")

            image_np = np.array(frame)
            
            # HSV & Rot-Masken
            hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)
            lower_red1 = np.array([0, 70, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 70, 50])
            upper_red2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = cv2.bitwise_or(mask1, mask2)

            # Rauschen entfernen & Konturen zählen
            kernel = np.ones((5, 5), np.uint8)
            mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            min_area = 50
            filtered = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

            st.success(f"🔴 Flecken gefunden: {len(filtered)}")

            # Ergebnisse anzeigen
            output = image_np.copy()
            cv2.drawContours(output, filtered, -1, (0, 255, 0), 2)
            st.image(output, caption="Markierte Flecken", channels="RGB")


if uploaded_file is not None:
    image_pil = Image.open(uploaded_file)

    # Mehrseitige Bilder prüfen (z. B. TIFF)
    try:
        frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(image_pil)]
    except Exception:
        frames = [image_pil.convert("RGB")]

    # Slider nur bei mehreren Seiten anzeigen
    if len(frames) > 1:
        page_index = st.slider("Seite auswählen", 0, len(frames)-1, 0)
    else:
        page_index = 0

    image = frames[page_index]
    image_np = np.array(image)

    # HSV-Konvertierung und Rot-Erkennung
    hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    # Rauschen entfernen
    kernel = np.ones((5, 5), np.uint8)
    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Konturen finden und filtern
    contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = 50
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

    st.success(f"🔴 Anzahl gefundener roter Flecken: {len(filtered_contours)}")

    # Ergebnisse anzeigen
    output_image = image_np.copy()
    cv2.drawContours(output_image, filtered_contours, -1, (0, 255, 0), 2)
    st.image(output_image, caption="Gefundene Flecken", channels="RGB")
