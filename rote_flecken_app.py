# app.py — Stufe 1.5: Analyse + Korrektur (Blob detection + radius filter)
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import cv2
import pandas as pd
import json
import io
import os
import time

# ---------------- config ----------------
st.set_page_config(page_title="Zellkern-Zähler Stufe 1.5", layout="wide")
st.title("🧬 Zellkern-Zähler — Stufe 1.5 (Analyse / Korrektur)")

PARAM_CSV = "parameter.csv"
FEEDBACK_JSON = "feedback.json"
os.makedirs("training_data", exist_ok=True)

# ---------------- helpers ----------------
def ensure_param_csv():
    if not os.path.exists(PARAM_CSV):
        df = pd.DataFrame(columns=[
            "timestamp", "name_pattern",
            "contrast", "mean_intensity", "height", "width",
            "min_area", "max_area", "min_circularity", "min_inertia_ratio"
        ])
        df.to_csv(PARAM_CSV, index=False)

def load_params_df():
    ensure_param_csv()
    return pd.read_csv(PARAM_CSV)

def save_param_example(features, params, name_pattern="*"):
    df = load_params_df()
    new = {
        "timestamp": time.time(),
        "name_pattern": name_pattern,
        "contrast": features["contrast"],
        "mean_intensity": features["mean_intensity"],
        "height": features["shape"][0],
        "width": features["shape"][1],
        "min_area": params["min_area"],
        "max_area": params["max_area"],
        "min_circularity": params["min_circularity"],
        "min_inertia_ratio": params["min_inertia_ratio"]
    }
    df = df.append(new, ignore_index=True)
    df.to_csv(PARAM_CSV, index=False)

def save_feedback(entry):
    db = []
    if os.path.exists(FEEDBACK_JSON):
        try:
            with open(FEEDBACK_JSON, "r") as f:
                db = json.load(f)
        except Exception:
            db = []
    db.append(entry)
    with open(FEEDBACK_JSON, "w") as f:
        json.dump(db, f, indent=2)

def get_image_features(img_gray):
    return {
        "contrast": float(img_gray.std()),
        "mean_intensity": float(img_gray.mean()),
        "shape": (int(img_gray.shape[0]), int(img_gray.shape[1]))
    }

def find_best_params_knn(features, df, k=3):
    if df.empty:
        return None
    # compute simple weighted distance
    def score(row):
        return (
            2.0 * abs(row["contrast"] - features["contrast"]) +
            1.0 * abs(row["mean_intensity"] - features["mean_intensity"]) +
            0.001 * (abs(row["height"] - features["shape"][0]) + abs(row["width"] - features["shape"][1]))
        )
    df["score"] = df.apply(score, axis=1)
    best = df.sort_values("score").head(k)
    if best.empty:
        return None
    # average numeric params
    out = {
        "min_area": int(round(best["min_area"].astype(float).mean())),
        "max_area": int(round(best["max_area"].astype(float).mean())),
        "min_circularity": float(best["min_circularity"].astype(float).mean()),
        "min_inertia_ratio": float(best["min_inertia_ratio"].astype(float).mean())
    }
    return out

def pil_open_rgb(uploaded_file):
    img = Image.open(uploaded_file)
    # if multiple frames, take first
    try:
        img.seek(0)
    except Exception:
        pass
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img

def create_blob_detector(min_area=30, max_area=5000, min_circularity=0.1, min_inertia_ratio=0.1):
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = max(1, min_area)
    params.maxArea = max(1, max_area)
    params.filterByCircularity = True
    params.minCircularity = float(min_circularity)
    params.filterByInertia = True
    params.minInertiaRatio = float(min_inertia_ratio)
    # do not filter by convexity by default
    params.filterByConvexity = False
    try:
        detector = cv2.SimpleBlobDetector_create(params)
    except AttributeError:
        detector = cv2.SimpleBlobDetector(params)
    return detector

def detect_nuclei_blobs(np_rgb, min_area, max_area, min_circularity, min_inertia_ratio):
    gray = cv2.cvtColor(np_rgb, cv2.COLOR_RGB2GRAY)
    # smoothing + CLAHE
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(blur)
    # invert if dark nuclei on light background (heuristic)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # prepare detector and detect
    detector = create_blob_detector(min_area, max_area, min_circularity, min_inertia_ratio)
    keypoints = detector.detect(thresh)
    centers = [(int(k.pt[0]), int(k.pt[1]), k.size/2.0) for k in keypoints]  # x, y, radius_px
    return centers

def map_canvas_to_original(obj_json, display_w, display_h, orig_w, orig_h):
    pts = []
    if not obj_json or "objects" not in obj_json:
        return pts
    sx = orig_w / display_w
    sy = orig_h / display_h
    for obj in obj_json["objects"]:
        left = obj.get("left", 0)
        top = obj.get("top", 0)
        w = obj.get("width", 0)
        h = obj.get("height", 0)
        cx = left + w/2
        cy = top + h/2
        orig_x = int(round(cx * sx))
        orig_y = int(round(cy * sy))
        pts.append((orig_x, orig_y))
    return pts

# ---------------- UI: Tabs ----------------
ensure_param_csv()
tab = st.tabs(["Analyse", "Korrektur"])
uploaded = None

with tab[0]:
    st.header("🔍 Analyse")
    uploaded = st.file_uploader("Bild (PNG/JPG/JPEG)", type=["png","jpg","jpeg"])
    if not uploaded:
        st.info("Bitte zuerst ein Bild hochladen (PNG, JPG, JPEG).")
        st.stop()

    pil_img = pil_open_rgb(uploaded)
    np_img = np.array(pil_img)
    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    features = get_image_features(gray)

    st.sidebar.header("⚙️ Analyse-Parameter (kann automatisch vorgeschlagen werden)")
    params_df = load_params_df = load_params_df = load_params_df = load_params_df if False else None  # placeholder to avoid lint noise
    params_df = pd.read_csv(PARAM_CSV)

    suggested = find_best_params_knn(features, params_df, k=3)  # may be None
    st.sidebar.markdown("**Vorgeschlagene Parameter (k-NN)**")
    st.sidebar.write(suggested if suggested else "Keine Vorschläge (noch keine Beispiele).")

    # allow user override
    min_area = st.sidebar.slider("Min area (px)", 5, 5000, int(suggested["min_area"]) if suggested else 30)
    max_area = st.sidebar.slider("Max area (px)", 50, 20000, int(suggested["max_area"]) if suggested else 5000)
    min_circularity = st.sidebar.slider("Min circularity", 0.0, 1.0, float(suggested["min_circularity"]) if suggested else 0.1, 0.01)
    min_inertia_ratio = st.sidebar.slider("Min inertia ratio", 0.0, 1.0, float(suggested["min_inertia_ratio"]) if suggested else 0.1, 0.01)

    # detection
    with st.spinner("Erkennung läuft..."):
        keypoints = detect_nuclei_blobs(np_img, min_area, max_area, min_circularity, min_inertia_ratio)
    st.success(f"Kerne gefunden: {len(keypoints)}")

    # show results side-by-side
    vis = np.array(pil_img).copy()
    for (x,y,r) in keypoints:
        cv2.circle(vis, (x,y), int(round(r)), (255,0,0), 2)  # red marker

    colA, colB = st.columns(2)
    colA.image(pil_img, caption="Original", use_container_width=True)
    colB.image(vis, caption=f"Automatisch (blau): {len(keypoints)}", use_container_width=True)

    # Quick stats
    sizes = [max(1, int(round(k[2]*2))) for k in keypoints]  # diameter px approx
    if sizes:
        st.markdown("**Statistik der erkannten Kerne**")
        st.write(f"- Mittel-Durchmesser (px): {np.mean(sizes):.1f}")
        st.write(f"- Median-Durchmesser (px): {np.median(sizes):.1f}")
        st.bar_chart(pd.Series(sizes).value_counts().sort_index())

    # Save suggested params as example
    st.markdown("### Parameter speichern")
    save_pattern = st.text_input("Name/Pattern für diese Parameter (optional)", value="*")
    if st.button("Als Beispiel-Parameter speichern"):
        save_param_example(features, {
            "min_area": int(min_area),
            "max_area": int(max_area),
            "min_circularity": float(min_circularity),
            "min_inertia_ratio": float(min_inertia_ratio)
        }, name_pattern=save_pattern)
        st.success("Parameterbeispiel gespeichert in parameter.csv")

with tab[1]:
    st.header("✏️ Korrektur")
    # Expect that user already uploaded in Analyse tab
    if "uploaded" not in locals() and uploaded is None:
        st.info("Bitte erst im Reiter 'Analyse' ein Bild hochladen und erkennen lassen.")
        st.stop()

    # re-open image and detection if needed
    pil_img = pil_open_rgb(uploaded)
    orig_w, orig_h = pil_img.size

    # We will re-run detection with last chosen parameters from Analyse tab if present in session_state
    # For simplicity, try to read last-saved suggested params from CSV nearest match
    gray = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
    features = get_image_features(gray)
    params_df = pd.read_csv(PARAM_CSV)
    suggested = find_best_params_knn(features, params_df, k=3)
    # default fallback
    min_area = int(suggested["min_area"]) if suggested is not None else 30
    max_area = int(suggested["max_area"]) if suggested is not None else 5000
    min_circularity = float(suggested["min_circularity"]) if suggested is not None else 0.1
    min_inertia_ratio = float(suggested["min_inertia_ratio"]) if suggested is not None else 0.1

    # run detection
    keypoints = detect_nuclei_blobs(np.array(pil_img), min_area, max_area, min_circularity, min_inertia_ratio)
    auto_centers = [(int(k[0]), int(k[1])) for k in keypoints]

    st.markdown(f"Automatisch erkannte Kerne: **{len(auto_centers)}** (Parameter aus Vorschlag / Default)")

    # scale for canvas display
    MAX_DIM = 1100
    scale = 1.0
    if max(orig_w, orig_h) > MAX_DIM:
        scale = MAX_DIM / max(orig_w, orig_h)
    display_w = int(round(orig_w * scale))
    display_h = int(round(orig_h * scale))
    if scale < 1.0:
        pil_for_canvas = pil_img.resize((display_w, display_h), Image.Resampling.LANCZOS)
    else:
        pil_for_canvas = pil_img

    # preview with auto points
    preview = np.array(pil_for_canvas).copy()
    vis_rad = 6
    for (x,y) in auto_centers:
        px = int(round(x * (display_w / orig_w)))
        py = int(round(y * (display_h / orig_h)))
        cv2.circle(preview, (px,py), vis_rad, (255,0,0), -1)

    st.image(preview, caption="Automatisch erkannte Punkte (rot)", use_container_width=True)

    st.markdown("**Interaktive Korrektur**: Oben grün = add, unten rot = remove. Klicks werden auf Original-Koordinaten zurückgerechnet.")
    st.write("Wenn du fertig bist, klicke 'Feedback speichern' — das speichert final points + meta in feedback.json")

    # green add canvas
    canvas_add = st_canvas(
        fill_color="",
        stroke_width=12,
        stroke_color="#00FF00",
        background_image=pil_for_canvas,
        update_streamlit=True,
        height=display_h,
        width=display_w,
        drawing_mode="point",
        point_display_radius=8,
        key="k_canvas_add"
    )

    # red remove canvas
    canvas_remove = st_canvas(
        fill_color="",
        stroke_width=12,
        stroke_color="#FF0000",
        background_image=pil_for_canvas,
        update_streamlit=True,
        height=display_h,
        width=display_w,
        drawing_mode="point",
        point_display_radius=8,
        key="k_canvas_remove"
    )

    # map clicks back to original coords
    added_pts = map_canvas_to_original(canvas_add.json_data if canvas_add else None, display_w, display_h, orig_w, orig_h)
    removed_pts = map_canvas_to_original(canvas_remove.json_data if canvas_remove else None, display_w, display_h, orig_w, orig_h)

    st.write(f"Hinzugefügt: {len(added_pts)} — Markiert zum Entfernen: {len(removed_pts)}")

    # combine
    def close_any(pt, pts, thr=10):
        return any(np.hypot(pt[0]-p[0], pt[1]-p[1]) < thr for p in pts)
    final_pts = [p for p in auto_centers if not close_any(p, removed_pts, thr=12)]
    for a in added_pts:
        if not close_any(a, final_pts, thr=6):
            final_pts.append(a)

    # show final preview
    final_preview = np.array(pil_for_canvas).copy()
    for (x,y) in final_pts:
        px = int(round(x * (display_w / orig_w)))
        py = int(round(y * (display_h / orig_h)))
        cv2.circle(final_preview, (px,py), vis_rad, (0,255,0), -1)
    st.image(final_preview, caption=f"Finale Punkte: {len(final_pts)}", use_container_width=True)

    # export and feedback save
    if len(final_pts) > 0:
        buf = io.StringIO()
        import csv
        w = csv.writer(buf)
        w.writerow(["X","Y"])
        w.writerows(final_pts)
        st.download_button("📥 Finale Punkte als CSV herunterladen", data=buf.getvalue().encode("utf-8"), file_name="zellkerne_final.csv", mime="text/csv")

    if st.button("💾 Feedback speichern (Parameters + Korrekturen)"):
        entry = {
            "timestamp": time.time(),
            "image_name": getattr(uploaded, "name", "uploaded_image"),
            "orig_shape": [orig_h, orig_w],
            "auto_count": len(auto_centers),
            "added_count": len(added_pts),
            "removed_count": len(removed_pts),
            "final_count": len(final_pts),
            "added_points": added_pts,
            "removed_points": removed_pts,
            "final_points": final_pts,
            "params_used": {
                "min_area": int(min_area),
                "max_area": int(max_area),
                "min_circularity": float(min_circularity),
                "min_inertia_ratio": float(min_inertia_ratio)
            }
        }
        save_feedback(entry)
        # also append param example to param csv for later suggestions
        save_param_example(get_image_features(cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)), entry["params_used"], name_pattern=getattr(uploaded, "name", "*"))
        st.success("Feedback + Parameter gespeichert.")

st.caption("Hinweis: diese Version nutzt OpenCV Blob-Detection als robuste, parameterbare Methode. \nGespeicherte Parameter findest du in parameter.csv, Feedback in feedback.json.")
