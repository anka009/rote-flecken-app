# app_single_view.py — Interaktive Korrektur in einem Bild
import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io
import csv

# Klick-Erfassung
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAVE_CLICK = True
except ImportError:
    HAVE_CLICK = False

st.set_page_config(page_title="🖌️ Objekte-Korrektur", layout="wide")
st.title("🖌️ Interaktive Korrektur im Einzelbild")

# Sidebar Einstellungen
st.sidebar.header("Einstellungen")
color_picker = st.sidebar.color_picker("Farbe der Markierung", "#ff0000")
line_thickness = st.sidebar.slider("Linienstärke", 1, 10, 2)
default_diameter = st.sidebar.slider("Standard-Durchmesser (px)", 2, 200, 20)

# Upload
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png", "jpg", "jpeg", "tif", "tiff"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    max_size = (1024, 1024)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Session State
    if "points" not in st.session_state:
        # speichert Elemente als (x, y, radius_px)
        st.session_state["points"] = []
    if "pending_point" not in st.session_state:
        # temporärer Klick ohne festgelegten Durchmesser
        st.session_state["pending_point"] = None

    st.write("**Korrektur:** Klicke auf bestehenden Kreis zum Löschen oder auf leeren Bereich zum Hinzufügen.")

    # Klick-Logik
    if HAVE_CLICK:
        coords = streamlit_image_coordinates(img, key="coords")
        if coords:
            x, y = int(coords["x"]), int(coords["y"])

            # Prüfen, ob Klick in bestehendem Kreis -> löschen
            removed = False
            for i, (px, py, pr) in enumerate(st.session_state["points"]):
                if (px - x) ** 2 + (py - y) ** 2 <= pr ** 2:
                    st.session_state["points"].pop(i)
                    removed = True
                    break

            # Falls nicht gelöscht -> neuen Kreis vorbereiten
            if not removed:
                st.session_state["pending_point"] = (x, y)

    # Popup-ähnliche Eingabe für Durchmesser
    if st.session_state["pending_point"] is not None:
        x, y = st.session_state["pending_point"]
        with st.container(border=True):
            st.markdown("#### Neuer Kreis")
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                diameter = st.number_input(
                    "Durchmesser (px)",
                    min_value=2, max_value=200, value=default_diameter, step=1,
                    key="diameter_input"
                )
            with col2:
                confirm = st.button("✅ Setzen", use_container_width=True, key="btn_set")
            with col3:
                cancel = st.button("❌ Abbrechen", use_container_width=True, key="btn_cancel")

        if confirm:
            st.session_state["points"].append((int(x), int(y), int(diameter // 2)))
            st.session_state["pending_point"] = None
            st.rerun()

        if cancel:
            st.session_state["pending_point"] = None
            st.rerun()

    # Bild mit Markierungen
    img_array = np.array(img)
    marked = img_array.copy()
    rgb_color = tuple(int(color_picker.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    bgr_color = rgb_color[::-1]

    for (x, y, r) in st.session_state["points"]:
        cv2.circle(marked, (x, y), r, bgr_color, line_thickness)

    # Anzeige + Zähler
    st.image(marked, caption=f"Markierte Objekte: {len(st.session_state['points'])}", use_column_width=True)

    # Zurücksetzen
    if st.button("🔄 Alle Punkte zurücksetzen"):
        st.session_state["points"] = []
        st.session_state["pending_point"] = None
        st.rerun()

    # CSV-Export
    if st.session_state["points"]:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["x", "y", "radius_px"])
        for (x, y, r) in st.session_state["points"]:
            writer.writerow([x, y, r])
        st.download_button(
            "📥 Punkte als CSV exportieren",
            data=buf.getvalue().encode("utf-8"),
            file_name="punkte.csv",
            mime="text/csv"
        )
else:
    st.info("Bitte ein Bild hochladen, um zu starten.")
