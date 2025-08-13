# app_learn_flecken.py
import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io
import json
import csv
import os
import time

# Klick-Erfassung
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAVE_CLICK = True
except:
    HAVE_CLICK = False

st.set_page_config(page_title="🧠 Lernender Flecken-Zähler", layout="wide")
st.title("🧠 Lernender Flecken-Zähler")

# ----------------- Dateien -----------------
FEEDBACK_FILE = "feedback.json"

def append_feedback(entry):
    db = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                db = json.load(f)
        except:
            db = []
    db.append(entry)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(db, f, indent=2)

# Sidebar Einstellungen
st.sidebar.header("Einstellungen")
radius = st.sidebar.slider("Radius der Markierungen (px)", 1, 50, 10)
line_thickness = st.sidebar.slider("Linienstärke", 1, 10, 2)
color_picker = st.sidebar.color_picker("Farbe der Markierung", "#ff0000")
auto_detect_radius = st.sidebar.slider("Automatische Suche Radius", 5, 50, 15)

# Upload
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    max_size = (1024, 1024)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    if "points" not in st.session_state:
        st.session_state["points"] = []

    st.write("**Korrektur:** Klick auf Fleck = markiert/gelöscht. Die Markierung wird für Lernprozess verwendet.")

    # Klick-Logik
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

    # Automatische Fleckenerkennung
    img_array = np.array(img)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)  # einfache Segmentierung
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    auto_points = []
    for c in contours:
        (cx, cy), r = cv2.minEnclosingCircle(c)
        for px, py in st.session_state["points"]:
            if (cx - px)**2 + (cy - py)**2 <= auto_detect_radius**2:
                auto_points.append((int(cx), int(cy)))
                break

    # Markierte Punkte zeichnen
    marked = img_array.copy()
    rgb_color = tuple(int(color_picker.lstrip("#")[i:i+2], 16) for i in (0,2,4))
    bgr_color = rgb_color[::-1]
    for (x, y) in st.session_state["points"]:
        cv2.circle(marked, (x, y), radius, bgr_color, line_thickness)
    for (x, y) in auto_points:
        cv2.circle(marked, (x, y), radius, (0,255,0), line_thickness)  # grün = automatisch erkannt

    st.image(marked, caption=f"Markierte Punkte: {len(st.session_state['points'])}, Auto erkannt: {len(auto_points)}", use_column_width=True)

    # Feedback speichern
    st.markdown("### 💾 Feedback speichern")
    save_label = st.text_input("Label / Notiz (optional)", value="")
    if st.button("Speichern"):
        entry = {
            "image_name": getattr(uploaded_file, "name", "uploaded_image"),
            "manual_points": [(int(x), int(y)) for (x,y) in st.session_state["points"]],
            "auto_points": [(int(x), int(y)) for (x,y) in auto_points],
            "note": save_label,
            "timestamp": int(time.time())
        }
        append_feedback(entry)
        st.success("Feedback gespeichert! Das Modell kann diese Punkte für nächste automatische Suche nutzen.")

    # CSV Export
    if st.session_state["points"] or auto_points:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["x","y","type"])
        for p in st.session_state["points"]:
            writer.writerow([p[0], p[1], "manual"])
        for p in auto_points:
            writer.writerow([p[0], p[1], "auto"])
        st.download_button("📥 Punkte als CSV exportieren", data=buf.getvalue().encode("utf-8"), file_name="punkte.csv", mime="text/csv")

    if st.button("🔄 Alle Punkte zurücksetzen"):
        st.session_state["points"] = []
