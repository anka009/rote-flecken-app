# lernender_flecken_zaehler.py
import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io
import json
import os
import time
import csv

# ----------------- Dateien -----------------
DB_FILE = "flecken_db.json"

# ----------------- Hilfsfunktionen -----------------
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def hsv_mask(img_rgb, lower_hsv, upper_hsv):
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))
    return mask

def detect_blobs(mask, min_area=20):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    results = []
    for c in contours:
        area = cv2.contourArea(c)
        if area >= min_area:
            (x,y), r = cv2.minEnclosingCircle(c)
            results.append({"x": int(x), "y": int(y), "radius": int(r), "area": float(area)})
    return results

def draw_points(img_rgb, points, color=(255,0,0), thickness=2):
    out = img_rgb.copy()
    for p in points:
        cv2.circle(out, (p["x"],p["y"]), p["radius"], color, thickness)
    return out

# ----------------- Streamlit -----------------
st.set_page_config(page_title="🧠 Lernender Flecken-Zähler", layout="wide")
st.title("🧠 Lernender Flecken-Zähler")

# Upload
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if not uploaded_file:
    st.info("Bitte Bild hochladen")
    st.stop()

img = Image.open(uploaded_file).convert("RGB")
img_array = np.array(img)

# Session state für Punkte
if "points" not in st.session_state:
    st.session_state["points"] = []

# Sidebar
st.sidebar.header("Markierungs-Einstellungen")
radius = st.sidebar.slider("Radius der Markierungen (px)", 1, 50, 10)
color_picker = st.sidebar.color_picker("Farbe der Markierung", "#ff0000")
thickness = st.sidebar.slider("Linienstärke", 1, 10, 2)
min_area = st.sidebar.slider("Min Area für automatische Erkennung", 5, 100, 20)

# Anzeige original + interaktiv
st.write("**Korrektur: Klick auf bestehenden Punkt zum Löschen, auf leeren Bereich zum Hinzufügen**")

# Klick-Erfassung
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    coords = streamlit_image_coordinates(img, key="coords")
    if coords:
        x, y = coords["x"], coords["y"]
        removed = False
        for i, p in enumerate(st.session_state["points"]):
            if (p["x"] - x)**2 + (p["y"] - y)**2 <= radius**2:
                st.session_state["points"].pop(i)
                removed = True
                break
        if not removed:
            st.session_state["points"].append({"x": x, "y": y, "radius": radius})
except ImportError:
    st.info("streamlit_image_coordinates nicht installiert, nur manuelle Eingabe möglich.")

# Automatische Erkennung basierend auf DB
db = load_db()
auto_points = []
for entry in db:
    hsv_lower = entry["lower_hsv"]
    hsv_upper = entry["upper_hsv"]
    mask = hsv_mask(img_array, hsv_lower, hsv_upper)
    auto_points.extend(detect_blobs(mask, min_area))

# Zusammenführen
all_points = st.session_state["points"] + auto_points

# Bild mit Punkten
rgb_color = tuple(int(color_picker.lstrip("#")[i:i+2],16) for i in (0,2,4))
bgr_color = rgb_color[::-1]
marked = draw_points(img_array, all_points, color=bgr_color, thickness=thickness)

st.image(marked, caption=f"Markierte Objekte: {len(all_points)}", use_column_width=True)

# Feedback speichern (lernen)
st.markdown("### Lernen speichern")
label = st.text_input("Label / Notiz")
if st.button("💾 Speichern"):
    # Einfacher Lern-Eintrag: HSV-Bereich automatisch anhand Klickpunkte
    if st.session_state["points"]:
        points_rgb = [img_array[p["y"],p["x"]] for p in st.session_state["points"]]
        points_hsv = [cv2.cvtColor(np.uint8([[c]]), cv2.COLOR_RGB2HSV)[0][0] for c in points_rgb]
        lower_hsv = np.min(points_hsv, axis=0).tolist()
        upper_hsv = np.max(points_hsv, axis=0).tolist()
        db.append({"lower_hsv": lower_hsv, "upper_hsv": upper_hsv, "label": label, "timestamp": int(time.time())})
        save_db(db)
        st.success("Gelernt und in DB gespeichert!")

# CSV Export
if all_points:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["x","y","radius"])
    for p in all_points:
        writer.writerow([p["x"],p["y"],p.get("radius",0)])
    st.download_button("📥 Punkte als CSV", data=buf.getvalue().encode("utf-8"), file_name="punkte.csv", mime="text/csv")

# Reset
if st.button("🔄 Alle Punkte zurücksetzen"):
    st.session_state["points"] = []
