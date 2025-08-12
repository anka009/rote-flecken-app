import streamlit as st
import cv2
import numpy as np
from PIL import Image
import json
import os
import io
import csv
import time

# optional für Klickkorrektur
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAVE_CLICK = True
except Exception:
    HAVE_CLICK = False

# Dateipfade
SETTINGS_FILE = "settings.json"
FEEDBACK_FILE = "feedback.json"

# ------------- Hilfsfunktionen -------------

def hsv_mask_from_sliders(img_rgb, lower_h, upper_h, lower_s, upper_s, lower_v, upper_v):
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    lower1 = np.array([lower_h, lower_s, lower_v])
    upper1 = np.array([upper_h, upper_s, upper_v])
    mask = cv2.inRange(hsv, lower1, upper1)
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
    for x,y,r,_ in points:
        cv2.circle(out, (x,y), int(r), color, thickness)
    return out

def points_to_csv_bytes(points):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["x","y","radius"])
    for p in points:
        writer.writerow([p[0], p[1], p[2]])
    return buf.getvalue().encode("utf-8")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
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
        except Exception:
            db = []
    db.append(entry)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(db, f, indent=2)

def extract_simple_features(img_rgb):
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    contrast = float(img_gray.std())
    mean_intensity = float(img_gray.mean())
    return {"contrast": contrast, "mean_intensity": mean_intensity}

def find_best_params(features, feedback_db):
    best_score = float('inf')
    best_params = None
    for entry in feedback_db:
        f = entry.get("features", {})
        if not f:
            continue
        score = abs(features["contrast"] - f.get("contrast", 0)) + abs(features["mean_intensity"] - f.get("mean_intensity", 0))
        if score < best_score:
            best_score = score
            best_params = entry.get("params_used", None)
    return best_params

# ------------- Streamlit UI -------------

st.set_page_config(page_title="Lernender Flecken-Zähler", layout="wide")
st.title("🧠 Lernender Flecken-Zähler — Lightweight Learning")

tabs = st.tabs(["🔍 Analyse", "✏️ Korrektur / Lernen", "⚙️ Einstellungen"])

# ---- Tab 1: Analyse ----
with tabs[0]:
    st.header("Analyse")
    uploaded = st.file_uploader("Bild (png/jpg/jpeg)", type=["png","jpg","jpeg"])
    if not uploaded:
        st.info("Bitte zuerst ein Bild hochladen.")
        st.stop()

    pil = Image.open(uploaded).convert("RGB")
    img_rgb = np.array(pil)

    # Feedback DB laden
    feedback_db = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                feedback_db = json.load(f)
        except Exception:
            feedback_db = []

    features = extract_simple_features(img_rgb)
    suggested_params = find_best_params(features, feedback_db)

    # Defaults aus Vorschlag oder Hardcoded
    default_lower_h = suggested_params.get("lower_h", 0) if suggested_params else 0
    default_upper_h = suggested_params.get("upper_h", 10) if suggested_params else 10
    default_lower_s = suggested_params.get("lower_s", 70) if suggested_params else 70
    default_upper_s = suggested_params.get("upper_s", 255) if suggested_params else 255
    default_lower_v = suggested_params.get("lower_v", 50) if suggested_params else 50
    default_upper_v = suggested_params.get("upper_v", 255) if suggested_params else 255
    default_min_radius = suggested_params.get("min_radius", 5) if suggested_params else 5
    default_min_area = suggested_params.get("min_area", 20) if suggested_params else 20

    st.sidebar.header("Erkennungs-Parameter (Slider)")
    lower_h = st.sidebar.slider("Lower H (OpenCV 0-179)", 0, 179, int(default_lower_h))
    upper_h = st.sidebar.slider("Upper H (OpenCV 0-179)", 0, 179, int(default_upper_h))
    lower_s = st.sidebar.slider("Lower S", 0, 255, int(default_lower_s))
    upper_s = st.sidebar.slider("Upper S", 0, 255, int(default_upper_s))
    lower_v = st.sidebar.slider("Lower V", 0, 255, int(default_lower_v))
    upper_v = st.sidebar.slider("Upper V", 0, 255, int(default_upper_v))
    min_radius_px = st.sidebar.slider("Min Radius (px)", 1, 200, int(default_min_radius))
    min_area_px = st.sidebar.slider("Min Contour Area (px)", 1, 10000, int(default_min_area))

    mask = hsv_mask_from_sliders(img_rgb, lower_h, upper_h, lower_s, upper_s, lower_v, upper_v)
    points = detect_blobs_from_mask(mask, min_radius_px, min_area_px)
    st.write(f"Gefundene Flecken (vor Korrektur): **{len(points)}**")

    mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
    marked = draw_points_on_image(img_rgb, points, color=(255,0,0), thickness=2)

    col1, col2 = st.columns(2)
    col1.image(Image.fromarray(mask_rgb), caption="Mask (HSV Filter)", use_container_width=True)
    col2.image(Image.fromarray(marked), caption="Erkannte Flecken (rot)", use_container_width=True)

    st.session_state["last_image"] = img_rgb
    st.session_state["detected_points"] = points
    st.session_state["params_being_used"] = {
        "lower_h": lower_h, "upper_h": upper_h,
        "lower_s": lower_s, "upper_s": upper_s,
        "lower_v": lower_v, "upper_v": upper_v,
        "min_radius": min_radius_px, "min_area": min_area_px
    }
    st.session_state["last_features"] = features

# ---- Tab 2: Korrektur / Lernen ----
with tabs[1]:
    st.header("Korrektur & Lernen")
    if "last_image" not in st.session_state:
        st.info("Bitte zuerst im Tab 'Analyse' ein Bild hochladen und analysieren.")
        st.stop()

    img_rgb = st.session_state["last_image"]
    detected = st.session_state.get("detected_points", [])
    orig_h, orig_w = img_rgb.shape[:2]

    disp = draw_points_on_image(img_rgb, detected, color=(255,0,0), thickness=2)
    st.image(Image.fromarray(disp), caption="Korrigieren: Klick zum Hinzufügen/Löschen", use_container_width=True)

    if HAVE_CLICK:
        st.info("Klicke auf existierenden Punkt zum Löschen, auf leeren Bereich zum Hinzufügen.")
        coords = streamlit_image_coordinates(Image.fromarray(disp), key="coords")
        if coords:
            cx, cy = coords["x"], coords["y"]
            removed = False
            for i, (px, py, pr, area) in enumerate(detected):
                if (px - cx)**2 + (py - cy)**2 <= (pr + 5)**2:
                    detected.pop(i)
                    removed = True
                    st.success(f"Punkt bei ({px},{py}) gelöscht.")
                    break
            if not removed:
                default_r = st.session_state["params_being_used"].get("min_radius", 10)
                detected.append((int(cx), int(cy), int(default_r), float(np.pi*default_r*default_r)))
                st.success(f"Punkt bei ({cx},{cy}) hinzugefügt.")
    else:
        st.info("Interaktive Klickkorrektur nicht verfügbar (streamlit-image-coordinates fehlt). Benutze manuelle Controls.")
        col1, col2 = st.columns(2)
        with col1:
            new_x = st.number_input("X hinzufügen", 0, orig_w-1, step=1)
            new_y = st.number_input("Y hinzufügen", 0, orig_h-1, step=1)
            new_r = st.number_input("Radius (px)", 1, 200, value=st.session_state["params_being_used"].get("min_radius",10))
            if st.button("Punkt hinzufügen (manuell)"):
                detected.append((int(new_x), int(new_y), int(new_r), float(np.pi*new_r*new_r)))
        with col2:
            if detected:
                idx = st.selectbox("Punkt auswählen zum Entfernen", list(range(len(detected))))
                if st.button("Ausgewählten Punkt entfernen"):
                    removed = detected.pop(idx)
                    st.info(f"Punkt {removed[0:3]} entfernt.")

    st.write(f"Aktuelle Flecken nach Korrektur: **{len(detected)}**")
    preview_after = draw_points_on_image(img_rgb, detected, color=(0,255,0), thickness=2)
    st.image(Image.fromarray(preview_after), caption="Nach Korrektur (grün)", use_container_width=True)

    st.markdown("### Speichern (Lernen)")
    save_label = st.text_input("Label / Notiz für dieses Feedback (optional)", value="")
    if st.button("💾 Korrektur & Parameter speichern"):
        params = st.session_state.get("params_being_used", {})
        settings_to_save = {
            "lower_h": int(params.get("lower_h", 0)),
            "upper_h": int(params.get("upper_h", 10)),
            "lower_s": int(params.get("lower_s", 70)),
            "upper_s": int(params.get("upper_s", 255)),
            "lower_v": int(params.get("lower_v", 50)),
            "upper_v": int(params.get("upper_v", 255)),
            "min_radius": int(params.get("min_radius", 5)),
            "min_area": int(params.get("min_area", 20)),
            "label": save_label,
            "timestamp": int(time.time())
        }
        save_settings(settings_to_save)

        entry = {
            "image_name": getattr(uploaded, "name", "uploaded_image"),
            "params_used": params,
            "final_points": [(int(x), int(y), int(r)) for (x,y,r,area) in detected],
            "count": len(detected),
            "note": save_label,
            "features": st.session_state.get("last_features", {})
        }
        append_feedback(entry)
        st.success("Korrektur + Parameter gespeichert. Werte werden beim nächsten Start als Voreinstellung geladen.")

    if detected:
        csv_bytes = points_to_csv_bytes(detected)
        st.download_button("📥 Finale Punkte als CSV herunterladen", data=csv_bytes, file_name="final_points.csv", mime="text/csv")

# ---- Tab 3: Einstellungen ----
with tabs[2]:
    st.header("Einstellungen & Speicher")
    st.write(f"Gespeicherte Einstellungsdatei: `{SETTINGS_FILE}`")
    st.write(f"Feedback-Datei: `{FEEDBACK_FILE}`")

    if os.path.exists(SETTINGS_FILE):
        st.write("Aktuelle saved settings:")
        try:
            with open(SETTINGS_FILE, "r") as f:
                st.json(json.load(f))
        except Exception:
            st.write("Fehler beim Lesen der settings.json")

    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                cnt = len(json.load(f))
        except Exception:
            cnt = "?"
        st.write(f"Feedback-Einträge: {cnt}")

    if st.button("❌ Alle gespeicherten Einstellungen & Feedback löschen"):
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)
        if os.path.exists(FEEDBACK_FILE):
            os.remove(FEEDBACK_FILE)
        st.experimental_rerun()
