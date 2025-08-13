# app_learning_flecken.py — Lernender interaktiver Flecken-Zähler
import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io
import csv
import json
import os

# Klick-Erfassung
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAVE_CLICK = True
except:
    HAVE_CLICK = False

st.set_page_config(page_title="🧠 Lernender Flecken-Zähler", layout="wide")
st.title("🧠 Lernender Flecken-Zähler — Interaktive Markierung + Auto-Erkennung")

# ---------------- Settings ----------------
st.sidebar.header("Einstellungen")
radius = st.sidebar.slider("Radius der Markierungen (px)", 1, 50, 10)
line_thickness = st.sidebar.slider("Linienstärke", 1, 10, 2)
color_picker_manual = st.sidebar.color_picker("Farbe manuelle Markierung", "#ff0000")
color_picker_auto = st.sidebar.color_picker("Farbe automatische Erkennung", "#00ff00")

# ---------------- Files ----------------
FEEDBACK_FILE = "flecken_feedback.json"

def load_feedback():
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_feedback(feedback_list):
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedback_list, f, indent=2)

# ---------------- Upload ----------------
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    max_size = (1024,1024)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    img_array = np.array(img)
    
    if "manual_points" not in st.session_state:
        st.session_state["manual_points"] = []
    if "auto_points" not in st.session_state:
        st.session_state["auto_points"] = []

    st.write("**Korrektur:** Klick auf leeren Bereich → Fleck markieren (manuell). Klick auf bestehenden Punkt → löschen.")

    # ---------------- Manual Marking ----------------
    if HAVE_CLICK:
        coords = streamlit_image_coordinates(img, key="coords")
        if coords:
            x, y = coords["x"], coords["y"]
            removed = False
            for i, (px, py, color) in enumerate(st.session_state["manual_points"]):
                if (px - x)**2 + (py - y)**2 <= radius**2:
                    st.session_state["manual_points"].pop(i)
                    removed = True
                    break
            if not removed:
                # Extract patch around clicked point
                patch_radius = radius
                x0, y0 = max(0, x-patch_radius), max(0, y-patch_radius)
                x1, y1 = min(img_array.shape[1], x+patch_radius), min(img_array.shape[0], y+patch_radius)
                patch = img_array[y0:y1, x0:x1]
                mean_color = patch.mean(axis=(0,1)).astype(int).tolist()  # RGB
                st.session_state["manual_points"].append((x, y, mean_color))

    # ---------------- Automatic Detection ----------------
    # Load feedback
    feedback_list = load_feedback()
    # For simplicity: consider each manual-marked color as "template"
    templates = [p[2] for p in feedback_list] + [p[2] for p in st.session_state["manual_points"]]

    # Find all contours
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    st.session_state["auto_points"] = []
    for c in contours:
        x_c, y_c, w_c, h_c = cv2.boundingRect(c)
        patch = img_array[y_c:y_c+h_c, x_c:x_c+w_c]
        mean_color_patch = patch.mean(axis=(0,1)).astype(int).tolist()
        # Compare with templates
        for template in templates:
            dist = np.linalg.norm(np.array(template) - np.array(mean_color_patch))
            if dist < 40:  # Threshold, kann angepasst werden
                cx, cy = x_c + w_c//2, y_c + h_c//2
                st.session_state["auto_points"].append((cx, cy, mean_color_patch))
                break

    # ---------------- Visualization ----------------
    marked = img_array.copy()
    # manual points
    rgb_manual = tuple(int(color_picker_manual.lstrip("#")[i:i+2],16) for i in (0,2,4))
    for x, y, _ in st.session_state["manual_points"]:
        cv2.circle(marked, (x, y), radius, rgb_manual[::-1], line_thickness)
    # auto points
    rgb_auto = tuple(int(color_picker_auto.lstrip("#")[i:i+2],16) for i in (0,2,4))
    for x, y, _ in st.session_state["auto_points"]:
        cv2.circle(marked, (x, y), radius, rgb_auto[::-1], line_thickness)

    st.image(marked, caption=f"Manuell: {len(st.session_state['manual_points'])} | Auto: {len(st.session_state['auto_points'])}", use_column_width=True)

    # ---------------- Feedback Speichern ----------------
    if st.button("💾 Manuelle Punkte als Feedback speichern"):
        feedback_list.extend(st.session_state["manual_points"])
        save_feedback(feedback_list)
        st.success(f"{len(st.session_state['manual_points'])} Punkte gespeichert.")

    # ---------------- CSV Export ----------------
    if st.session_state["manual_points"] or st.session_state["auto_points"]:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["x","y","R","G","B","type"])
        for x, y, color in st.session_state["manual_points"]:
            writer.writerow([x, y, color[0], color[1], color[2], "manual"])
        for x, y, color in st.session_state["auto_points"]:
            writer.writerow([x, y, color[0], color[1], color[2], "auto"])
        st.download_button("📥 Punkte als CSV exportieren", data=buf.getvalue().encode("utf-8"), file_name="punkte.csv", mime="text/csv")

    # ---------------- Reset ----------------
    if st.button("🔄 Alle Punkte zurücksetzen"):
        st.session_state["manual_points"] = []
        st.session_state["auto_points"] = []
