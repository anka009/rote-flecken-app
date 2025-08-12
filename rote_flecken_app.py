import streamlit as st
import numpy as np
import cv2
from PIL import Image

st.set_page_config(layout="wide")
st.title("🎯 Farb-Flecken-Zähler")

uploaded_file = st.file_uploader("📁 Bild hochladen", type=["jpg", "png", "tif", "tiff"])
if uploaded_file:
    image = np.array(Image.open(uploaded_file).convert("RGB"))
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

    # 🎨 Farbgrenzen definieren
    def count_color(hsv_img, lower, upper):
        mask = cv2.inRange(hsv_img, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return len([c for c in contours if cv2.contourArea(c) > 50])

    # 🔴 Rot
    red1 = count_color(hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
    red2 = count_color(hsv, np.array([160, 70, 50]), np.array([180, 255, 255]))
    red_count = red1 + red2

    # 🟢 Grün
    green_count = count_color(hsv, np.array([40, 70, 50]), np.array([80, 255, 255]))

    # 🔵 Blau
    blue_count = count_color(hsv, np.array([100, 70, 50]), np.array([140, 255, 255]))

    # ⚫ Dunkel (niedrige Helligkeit)
    dark_mask = cv2.inRange(hsv[:, :, 2], 0, 50)
    contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    dark_count = len([c for c in contours if cv2.contourArea(c) > 50])

    # 🖼️ Anzeige
    st.image(image, caption="📷 Originalbild", use_column_width=True)

    # 📊 Live-Zähler
    st.markdown("### 📊 Fleckenanzahl (live)")
    st.metric("🔴 Rote Flecken", red_count)
    st.metric("🟢 Grüne Flecken", green_count)
    st.metric("🔵 Blaue Flecken", blue_count)
    st.metric("⚫ Dunkle Flecken", dark_count)
