import streamlit as st
import cv2
import numpy as np
from PIL import Image
import json
import os
import io
import csv
import time

# ----------------- Dateien -----------------
SETTINGS_FILE = "settings.json"   # speichert letzte Parameter
FEEDBACK_FILE = "feedback.json"   # speichert Korrekturen / Historie

# ----------------- Hilfsfunktionen -----------------
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(d):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(d, f, indent=2)

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

def hsv_mask_from_sliders(img_rgb, lower_h, upper_h, lower_s, upper_s, lower_v, upper_v):
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    lower = np.array([lower_h, lower_s, lower_v])
    upper = np.array([upper_h, upper_s, upper_v])
    mask = cv2.inRange(hsv, lower, upper)
    return mask

def detect_blobs_from_mask(mask, min_radius_px=5, min_area_px=20):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    results = []
    for c in contours:
        (x, y), r = cv2.minEnclosingCircle(c)
        area = cv2.contourArea(c)
        if r >= min_radius_px and area >= min_area_px:
            results.append((int(round(x)), int(round(y)), int(round(r)), float(area)))
    return results

def draw_points_on_image(img_rgb, points, color=(255,0,0), thickness=2):
    out = img_rgb.copy()
    for x, y, r, _ in points:
        cv2.circle(out, (x, y), int(r), color, thickness)
    return out

def points_to_csv_bytes(points):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["x","y","radius"])
    for p in points:
        writer.writerow([p[0], p[1], p[2]])
    return buf.getvalue().encode("utf-8")

# ----------------- Streamlit -----------------
st.set_page_config(page_title="Stufe 2.0: Lernender Flecken-Zähler", layout="wide")
st.title("🧠 Lernender Flecken-Zähler — Stufe 2.0")

# Load last settings
last_settings = load_settings()
default_lower_h = last_settings.get("lower_h", 0)
default_upper_h = last_settings.get("upper_h", 10)
default_lower_s = last_settings.get("lower_s", 70)
default_upper_s = last_settings.get("upper_s", 255)
default_lower_v = last_settings.get("lower_v", 50)
default_upper_v = last_settings.get("upper_v", 255)
default_min_radius = last_settings.get("min_radius", 5)
default_min_area = last_settings.get("min_area", 20)

# ----------------- Tabs -----------------
tabs = st.tabs(["🔍 Analyse", "✏️ Korrektur & Lernen", "⚙️ Einstellungen"])

# ---------------- Tab 1: Analyse ----------------
with tabs[0]:
    st.header("Analyse")
    uploaded = st.file_uploader("Bild hochladen (PNG/JPG/TIF/TIFF)", type=["png","jpg","jpeg","tif","tiff"])
    if not uploaded:
        st.info("Bitte zuerst ein Bild hochladen.")
        st.stop()
    pil = Image.open(uploaded).convert("RGB")
    img_rgb = np.array(pil)

    st.sidebar.header("Parameter")
    lower_h = st.sidebar.slider("Lower H", 0, 179, int(default_lower_h))
    upper_h = st.sidebar.slider("Upper H", 0, 179, int(default_upper_h))
    lower_s = st.sidebar.slider("Lower S", 0, 255, int(default_lower_s))
    upper_s = st.sidebar.slider("Upper S", 0, 255, int(default_upper_s))
    lower_v = st.sidebar.slider("Lower V", 0, 255, int(default_lower_v))
    upper_v = st.sidebar.slider("Upper V", 0, 255, int(default_upper_v))
    min_radius_px = st.sidebar.slider("Min Radius (px)", 1, 200, int(default_min_radius))
    min_area_px = st.sidebar.slider("Min Area (px)", 1, 10000, int(default_min_area))

    # Mask + Detection
    mask = hsv_mask_from_sliders(img_rgb, lower_h, upper_h, lower_s, upper_s, lower_v, upper_v)
    points = detect_blobs_from_mask(mask, min_radius_px, min_area_px)
    st.write(f"Gefundene Flecken: **{len(points)}**")

    mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
    marked = draw_points_on_image(img_rgb, points, color=(255,0,0), thickness=2)

    col1, col2 = st.columns(2)
    col1.image(Image.fromarray(mask_rgb), caption="Mask", use_container_width=True)
    col2.image(Image.fromarray(marked), caption="Erkannte Flecken (rot)", use_container_width=True)

    # save to session
    st.session_state["last_image"] = img_rgb
    st.session_state["detected_points"] = points
    st.session_state["params"] = {
        "lower_h": lower_h, "upper_h": upper_h,
        "lower_s": lower_s, "upper_s": upper_s,
        "lower_v": lower_v, "upper_v": upper_v,
        "min_radius": min_radius_px, "min_area": min_area_px
    }

# ---------------- Tab 2: Korrektur & Lernen ----------------
with tabs[1]:
    st.header("Korrektur & Lernen")
    if "last_image" not in st.session_state:
        st.info("Bitte zuerst im Tab 'Analyse' ein Bild hochladen und analysieren.")
        st.stop()
    img_rgb = st.session_state["last_image"]
    detected = st.session_state.get("detected_points", [])

    # show current points
    st.write("Erkannte + hinzugefügte Punkte (rot: automatisch, grün: manuell korrigiert)")
    preview = draw_points_on_image(img_rgb, detected, color=(0,255,0), thickness=2)
    st.image(Image.fromarray(preview), use_container_width=True)

    # manuelle Korrektur
    st.markdown("### Punkt hinzufügen / entfernen")
    col1, col2 = st.columns(2)
    with col1:
        new_x = st.number_input("X hinzufügen", 0, img_rgb.shape[1]-1, step=1)
        new_y = st.number_input("Y hinzufügen", 0, img_rgb.shape[0]-1, step=1)
        new_r = st.number_input("Radius (px)", 1, 200, value=st.session_state["params"]["min_radius"])
        if st.button("Punkt hinzufügen"):
            detected.append((int(new_x), int(new_y), int(new_r), float(np.pi*new_r*new_r)))
            st.success(f"Punkt bei ({new_x},{new_y}) hinzugefügt.")

    with col2:
        if detected:
            idx = st.selectbox("Punkt auswählen zum Entfernen", list(range(len(detected))))
            if st.button("Punkt entfernen"):
                removed = detected.pop(idx)
                st.info(f"Punkt {removed[0:3]} entfernt.")

    st.session_state["detected_points"] = detected
    st.write(f"Aktuelle Punkte nach Korrektur: **{len(detected)}**")
    preview_after = draw_points_on_image(img_rgb, detected, color=(0,255,0), thickness=2)
    st.image(Image.fromarray(preview_after), caption="Vorschau nach Korrektur", use_container_width=True)

    # Speichern + Feedback
    st.markdown("### Feedback speichern / Lernen")
    save_label = st.text_input("Label / Notiz für dieses Feedback (optional)", value="")
    if st.button("💾 Korrektur & Parameter speichern"):
        params = st.session_state.get("params", {})
        save_settings(params)
        entry = {
            "image_name": getattr(uploaded, "name", "uploaded_image"),
            "params_used": params,
            "final_points": [(int(x), int(y), int(r)) for (x,y,r,_) in detected],
            "count": len(detected),
            "note": save_label,
            "timestamp": int(time.time())
        }
        append_feedback(entry)
        st.success("Korrektur + Parameter gespeichert.")

    # CSV Download
    if detected:
        csv_bytes = points_to_csv_bytes(detected)
        st.download_button("📥 Finale Punkte als CSV herunterladen", data=csv_bytes, file_name="final_points.csv", mime="text/csv")

# ---------------- Tab 3: Einstellungen ----------------
with tabs[2]:
    st.header("Einstellungen & Feedback")
    st.write("Settings-Datei:", SETTINGS_FILE)
    st.write("Feedback-Datei:", FEEDBACK_FILE)
    if os.path.exists(SETTINGS_FILE):
        st.json(load_settings())
    if os.path.exists(FEEDBACK_FILE):
        try:
            cnt = len(json.load(open(FEEDBACK_FILE)))
        except:
            cnt = "?"
        st.write(f"Feedback-Einträge: {cnt}")

    if st.button("❌ Alle gespeicherten Einstellungen & Feedback löschen"):
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)
        if os.path.exists(FEEDBACK_FILE):
            os.remove(FEEDBACK_FILE)
        st.experimental_rerun()
