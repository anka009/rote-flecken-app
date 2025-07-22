import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.title("🔴 Rote Flecken Zähler")

uploaded_file = st.file_uploader("Lade ein Bild hoch", type=["jpg", "jpeg", "png", "tif", "tiff"])
from PIL import Image, ImageSequence

if uploaded_file is not None:
    tiff_image = Image.open(uploaded_file)
    
    # Alle Seiten extrahieren
    frames = [page.convert("RGB") for page in ImageSequence.Iterator(tiff_image)]
    
    # Wähle eine Seite (z.B. die erste)
    image = frames[0]
page_index = st.slider("Seite auswählen", 0, len(frames)-1, 0)
image = frames[page_index]
from PIL import Image, ImageSequence

if uploaded_file is not None:
    tiff_image = Image.open(uploaded_file)
    
    # Seiten extrahieren, funktioniert auch für JPG & PNG
    try:
        frames = [page.convert("RGB") for page in ImageSequence.Iterator(tiff_image)]
    except:
        frames = [tiff_image.convert("RGB")]

    # Auswahl-Slider anzeigen
    page_index = st.slider("Seite auswählen", 0, len(frames)-1, 0)
    image = frames[page_index]

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    image_np = np.array(image)

    # Bild in HSV umwandeln
    hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

    # Rot-Masken erstellen
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

    # Konturen finden
    contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Kleine Objekte filtern
    min_area = 50
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

    # Ergebnisse anzeigen
    st.success(f"🔴 Anzahl gefundener roter Flecken: {len(filtered_contours)}")

    # Konturen ins Bild einzeichnen
    output_image = image_np.copy()
    cv2.drawContours(output_image, filtered_contours, -1, (0, 255, 0), 2)

    st.image(output_image, caption="Gefundene Flecken", channels="RGB")
