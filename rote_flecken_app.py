import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageSequence

st.title("🔬 Rote Flecken Analyse")

uploaded_files = st.file_uploader(
    "📁 Lade mehrere Bilder hoch",
    type=["jpg", "jpeg", "png", "tif", "tiff"],
    accept_multiple_files=True
)

# Optional: DPI für physikalische Umrechnung
dpi = 300  # Wenn bekannt
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
            frames = [Image.open(uploaded_file).convert("RGB")]
# 📄 Bildverarbeitung pro Frame
for i, frame in enumerate(frames):
    if len(frames) > 1:
        st.subheader(f"📄 Seite {i+1}")

    image_np = np.array(frame)

    # 🎨 Farbkonvertierung zu HSV
    hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

    # 🟥 Farbgrenzen definieren
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    lower_brown = np.array([10, 100, 20])      # Braunrot
    upper_brown = np.array([30, 255, 200])

    # 🧪 Masken erstellen und kombinieren
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask3 = cv2.inRange(hsv, lower_brown, upper_brown)
    combined_mask = cv2.bitwise_or(mask1, mask2)
    mask = cv2.bitwise_or(combined_mask, mask3)

    # 🧹 Maske säubern
    kernel = np.ones((5, 5), np.uint8)
    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # 🔍 Konturen finden
    contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = 50
    filtered = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

    # 📊 Berechnung pro Frame
    fleckenzahl = len(filtered)
    fläche_pixel = sum(cv2.contourArea(cnt) for cnt in filtered)
    fläche_mm2 = fläche_pixel / (pixels_per_mm ** 2)

    st.success(f"🔴 Flecken gefunden: {fleckenzahl}")
    st.info(f"📐 Fläche: {fläche_pixel:.2f} Pixel² ({fläche_mm2:.2f} mm²)")

    # 📦 Gesamtsummen aktualisieren
    total_flecken += fleckenzahl
    total_pixel_area += fläche_pixel

    # 🖼️ Bild mit Konturen anzeigen
    output = image_np.copy()
    cv2.drawContours(output, filtered, -1, (0, 255, 0), 2)
    st.image(output, caption="Markierte Flecken", channels="RGB")

# 📊 Gesamtauswertung
total_mm2 = total_pixel_area / (pixels_per_mm ** 2)
st.markdown("---")
st.subheader("📊 Gesamtanalyse")
st.success(f"🔴 Gesamtanzahl Flecken: {total_flecken}")
st.info(f"📐 Gesamtfläche: {total_pixel_area:.2f} Pixel² ({total_mm2:.2f} mm²)")

