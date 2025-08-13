# stufe3_app.py — Lernender Flecken-Zähler 3.0
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import json
import os
import io
import csv

try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    HAVE_CLICK = True
except Exception:
    HAVE_CLICK = False

SETTINGS_FILE = "settings.json"
FEEDBACK_FILE = "feedback.json"

# ----------------- Hilfsfunktionen -----------------
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
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

# ----------------- Streamlit -----------------
st.set_page_config(page_title="Lernender Flecken-Zähler 3.0", layout="wide")
st.title("🧠 Lernender Flecken-Zähler 3.0")

# Lade letzte Einstellungen
last_settings = load_settings()
default_params = {
    "lower_h": last_settings.get("lower_h",0),
    "upper_h": last_settings.get("upper_h",10),
    "lower_s": last_settings.get("lower_s",70),
    "upper_s": last_settings.get("upper_s",255),
    "lower_v": last_settings.get("lower_v",50),
    "upper_v": last_settings.get("upper_v",255),
    "min_radius": last_settings.get("min_radius",5),
    "min_area": last_settings.get("min_area",20)
}

# Tabs: Analyse / Korrektur / Einstellungen
tabs = st.tabs(["🔍 Analyse", "✏️ Korrektur / Lernen", "⚙️ Einstellungen"])

# ---------------- Tab Analyse ----------------
with tabs[0]:
    st.header("Analyse")
    uploaded = st.file_uploader("Bild (png/jpg/jpeg/tif/tiff)", type=["png","jpg","jpeg","tif","tiff"])
    if not uploaded:
        st.info("Bitte zuerst ein Bild hochladen.")
        st.stop()

    pil = Image.open(uploaded).convert("RGB")
    img_rgb = np.array(pil)

    st.sidebar.header("Erkennungs-Parameter")
    lower_h = st.sidebar.slider("Lower H", 0,179, default_params["lower_h"])
    upper_h = st.sidebar.slider("Upper H", 0,179, default_params["upper_h"])
    lower_s = st.sidebar.slider("Lower S", 0,255, default_params["lower_s"])
    upper_s = st.sidebar.slider("Upper S", 0,255, default_params["upper_s"])
    lower_v = st.sidebar.slider("Lower V", 0,255, default_params["lower_v"])
    upper_v = st.sidebar.slider("Upper V", 0,255, default_params["upper_v"])
    min_radius_px = st.sidebar.slider("Min Radius", 1,200, default_params["min_radius"])
    min_area_px = st.sidebar.slider("Min Area",1,10000, default_params["min_area"])

    mask = hsv_mask_from_sliders(img_rgb, lower_h, upper_h, lower_s, upper_s, lower_v, upper_v)
    auto_points = detect_blobs_from_mask(mask, min_radius_px, min_area_px)
    st.write(f"Automatisch gefundene Flecken: **{len(auto_points)}**")

    mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
    marked_auto = draw_points_on_image(img_rgb, auto_points, color=(255,0,0), thickness=2)

    col1, col2 = st.columns(2)
    col1.image(Image.fromarray(mask_rgb), caption="Mask (HSV Filter)", use_container_width=True)
    col2.image(Image.fromarray(marked_auto), caption="Erkannte Flecken (rot)", use_container_width=True)

    # Speicher für Korrektur-Tab
    st.session_state["last_image"] = img_rgb
    st.session_state["auto_points"] = auto_points
    st.session_state["manual_points"] = []

# ---------------- Tab Korrektur / Lernen ----------------
with tabs[1]:
    st.header("Korrektur & Lernen")
    if "last_image" not in st.session_state:
        st.info("Bitte zuerst im Tab 'Analyse' ein Bild hochladen und analysieren.")
        st.stop()

    img_rgb = st.session_state["last_image"]
    auto_points = st.session_state.get("auto_points",[])
    manual_points = st.session_state.get("manual_points",[])

    # Kombiniertes Bild
    combined_disp = draw_points_on_image(img_rgb, auto_points, color=(255,0,0), thickness=2)
    combined_disp = draw_points_on_image(combined_disp, manual_points, color=(0,255,0), thickness=2)
    st.image(Image.fromarray(combined_disp), caption="Rot=Auto, Grün=Manuell", use_container_width=True)

    if HAVE_CLICK:
        st.info("Klick auf roten Punkt: löschen; Klick auf leeren Bereich: hinzufügen")
        coords = streamlit_image_coordinates(Image.fromarray(combined_disp), key="coords_corr")
        if coords:
            cx, cy = coords["x"], coords["y"]
            clicked = False
            # Prüfe manuelle Punkte zuerst
            for i, (px,py,pr,area) in enumerate(manual_points):
                if (px-cx)**2+(py-cy)**2 <= (pr+5)**2:
                    manual_points.pop(i)
                    st.success(f"Manueller Punkt bei ({px},{py}) gelöscht")
                    clicked = True
                    break
            if not clicked:
                # Prüfe auto Punkte -> löschen nicht, nur add?
                default_r = 10
                manual_points.append((cx,cy,default_r,float(np.pi*default_r*default_r)))
                st.success(f"Neuer manueller Punkt bei ({cx},{cy}) hinzugefügt")
        st.session_state["manual_points"] = manual_points
    else:
        st.info("streamlit_image_coordinates nicht installiert -> nur manuelle Eingabe")
        col1, col2 = st.columns(2)
        with col1:
            new_x = st.number_input("X hinzufügen",0,img_rgb.shape[1]-1, step=1)
            new_y = st.number_input("Y hinzufügen",0,img_rgb.shape[0]-1, step=1)
            new_r = st.number_input("Radius",1,200,value=10)
            if st.button("Punkt hinzufügen"):
                manual_points.append((new_x,new_y,new_r,float(np.pi*new_r*new_r)))
        with col2:
            if manual_points:
                idx = st.selectbox("Punkt entfernen", list(range(len(manual_points))))
                if st.button("Entfernen"):
                    removed = manual_points.pop(idx)
                    st.info(f"Punkt {removed[0:3]} entfernt")

    # Vorschau + CSV Export
    final_points = auto_points + manual_points
    st.write(f"Endgültige Flecken nach Korrektur: **{len(final_points)}**")
    preview = draw_points_on_image(img_rgb, final_points, color=(0,255,0), thickness=2)
    st.image(Image.fromarray(preview), caption="Alle Flecken (Grün)")

    csv_bytes = points_to_csv_bytes(final_points)
    st.download_button("📥 Finale Punkte CSV herunterladen", data=csv_bytes, file_name="final_points.csv", mime="text/csv")

    # Feedback speichern
    label = st.text_input("Label / Notiz für Feedback", value="")
    if st.button("💾 Feedback & Parameter speichern"):
        settings_to_save = {
            "lower_h": lower_h, "upper_h": upper_h,
            "lower_s": lower_s, "upper_s": upper_s,
            "lower_v": lower_v, "upper_v": upper_v,
            "min_radius": min_radius_px, "min_area": min_area_px,
            "label": label
        }
        save_settings(settings_to_save)
        entry = {
            "image_name": getattr(uploaded,"name","uploaded_image"),
            "params": settings_to_save,
            "auto_points": auto_points,
            "manual_points": manual_points,
            "count_total": len(final_points),
            "note": label
        }
        append_feedback(entry)
        st.success("Feedback gespeichert!")

# ---------------- Tab Einstellungen ----------------
with tabs[2]:
    st.header("Einstellungen & Feedback")
    st.write("Gespeicherte Einstellungen:", SETTINGS_FILE)
    st.write("Feedback-Datei:", FEEDBACK_FILE)
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE,"r") as f:
            st.json(json.load(f))
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE,"r") as f:
            st.write(f"{len(json.load(f))} Feedback-Einträge")
    if st.button("❌ Alles löschen"):
        if os.path.exists(SETTINGS_FILE): os.remove(SETTINGS_FILE)
        if os.path.exists(FEEDBACK_FILE): os.remove(FEEDBACK_FILE)
        st.experimental_rerun()
