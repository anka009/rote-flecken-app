# app_stufe2.py
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

# ML libs
try:
    from sklearn.ensemble import RandomForestClassifier
    import joblib
except Exception:
    RandomForestClassifier = None
    joblib = None

# ---------------- config ----------------
st.set_page_config(page_title="Zellkern-Zähler Stufe 2", layout="wide")
st.title("🧬 Zellkern-Zähler — Stufe 2 (Interaktiv + Lernend)")

PARAM_CSV = "parameter.csv"
FEEDBACK_JSON = "feedback.json"
MODEL_FILE = "model.pkl"
os.makedirs("training_data", exist_ok=True)

# ---------------- helpers ----------------
def pil_open_rgb(uploaded_file):
    img = Image.open(uploaded_file)
    try: img.seek(0)
    except Exception: pass
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img

def detect_nuclei_blobs(np_rgb, min_area, max_area, min_circularity, min_inertia_ratio):
    gray = cv2.cvtColor(np_rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(blur)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    detector = create_blob_detector(min_area, max_area, min_circularity, min_inertia_ratio)
    keypoints = detector.detect(thresh)
    centers = [(int(k.pt[0]), int(k.pt[1]), k.size/2.0) for k in keypoints]
    return centers

def create_blob_detector(min_area=30, max_area=5000, min_circularity=0.1, min_inertia_ratio=0.1):
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = max(1, min_area)
    params.maxArea = max(1, max_area)
    params.filterByCircularity = True
    params.minCircularity = float(min_circularity)
    params.filterByInertia = True
    params.minInertiaRatio = float(min_inertia_ratio)
    params.filterByConvexity = False
    try:
        detector = cv2.SimpleBlobDetector_create(params)
    except AttributeError:
        detector = cv2.SimpleBlobDetector(params)
    return detector

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

def close_to_any(pt, pts, thr=8):
    return any(np.hypot(pt[0]-p[0], pt[1]-p[1]) < thr for p in pts)

# --- Feature extraction for ML ---
def extract_point_features(np_rgb, points, patch=21):
    """
    points: list of (x,y,radius) or (x,y)
    returns X: list of feature vectors [mean, std, local_contrast, laplace_var, radius]
    """
    gray = cv2.cvtColor(np_rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    half = patch // 2
    feats = []
    for p in points:
        x, y = int(p[0]), int(p[1])
        r = p[2] if len(p) > 2 else 3.0
        x0 = max(0, x-half); x1 = min(w, x+half+1)
        y0 = max(0, y-half); y1 = min(h, y+half+1)
        patch_img = gray[y0:y1, x0:x1]
        if patch_img.size == 0:
            feats.append([0,0,0,0,float(r)])
            continue
        mean = float(patch_img.mean())
        std = float(patch_img.std())
        local_contrast = float(np.percentile(patch_img,90) - np.percentile(patch_img,10))
        lap = cv2.Laplacian(patch_img, cv2.CV_64F)
        lap_var = float(lap.var())
        feats.append([mean, std, local_contrast, lap_var, float(r)])
    return np.array(feats, dtype=float)

# --- Build training dataset from feedback.json ---
def build_training_data(feedback_json_path):
    if not os.path.exists(feedback_json_path):
        return None, None
    with open(feedback_json_path, "r") as f:
        db = json.load(f)
    X_list = []
    y_list = []
    for entry in db:
        # find positives = final_points
        final = entry.get("final_points", [])
        removed = entry.get("removed_points", [])
        orig_shape = entry.get("orig_shape", None)
        # need the image file to extract patch features; if not present, skip those entries
        img_name = entry.get("image_name", None)
        # If the image exists locally, open it; else we cannot extract patch-features -> skip
        if img_name and os.path.exists(img_name):
            pil = Image.open(img_name).convert("RGB")
            np_img = np.array(pil)
            # positives
            pos_feats = extract_point_features(np_img, [(x,y) for (x,y) in final])
            if pos_feats.size>0:
                X_list.append(pos_feats); y_list += [1]*len(pos_feats)
            # negatives: use removed_points
            neg_feats = extract_point_features(np_img, [(x,y) for (x,y) in removed])
            if neg_feats.size>0:
                X_list.append(neg_feats); y_list += [0]*len(neg_feats)
        else:
            # If image not available, we can still use coordinates? skip — require image files for features
            continue
    if len(X_list)==0:
        return None, None
    X = np.vstack(X_list)
    y = np.array(y_list, dtype=int)
    return X, y

# --- Train / Load model ---
def train_and_save_model(X, y, model_path=MODEL_FILE):
    if RandomForestClassifier is None:
        raise RuntimeError("scikit-learn is required. Install with: pip install scikit-learn joblib")
    clf = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
    clf.fit(X, y)
    joblib.dump(clf, model_path)
    return clf

def load_model(model_path=MODEL_FILE):
    if joblib is None:
        return None
    if os.path.exists(model_path):
        try:
            return joblib.load(model_path)
        except Exception:
            return None
    return None

# ---------------- UI ----------------
st.sidebar.header("Model")
model = load_model()
if model is None:
    st.sidebar.info("Kein Modell gefunden. Sammle Feedback und trainiere ein Modell (Tab 'Korrektur').")
else:
    st.sidebar.success("Modell geladen: " + MODEL_FILE)

tabs = st.tabs(["Analyse", "Korrektur", "Model-Train"])

# ---------- Analyse Tab ----------
with tabs[0]:
    st.header("🔍 Analyse")
    uploaded = st.file_uploader("Bild (PNG/JPG/JPEG)", type=["png","jpg","jpeg"])
    if not uploaded:
        st.info("Bitte ein Bild hochladen.")
        st.stop()
    pil_img = pil_open_rgb(uploaded)
    np_img = np.array(pil_img)
    orig_w, orig_h = pil_img.size

    # parameter UI (simple defaults)
    st.sidebar.header("Erkennungsparameter")
    min_area = st.sidebar.slider("Min area (px)", 5, 5000, 30)
    max_area = st.sidebar.slider("Max area (px)", 50, 20000, 5000)
    min_circularity = st.sidebar.slider("Min circularity", 0.0, 1.0, 0.1, 0.01)
    min_inertia_ratio = st.sidebar.slider("Min inertia ratio", 0.0, 1.0, 0.1, 0.01)

    # detect
    with st.spinner("Erkennung läuft..."):
        keypoints = detect_nuclei_blobs(np_img, min_area, max_area, min_circularity, min_inertia_ratio)
    st.success(f"Kerne gefunden: {len(keypoints)}")

    # If model exists, get probabilities and filter
    apply_model = st.sidebar.checkbox("Modell anwenden (Filter false-positives)", value=True)
    threshold = st.sidebar.slider("Wahrscheinlichkeitsschwelle", 0.0, 1.0, 0.5, 0.01)
    if model is not None and apply_model:
        # prepare points for prediction (use x,y,r)
        pts = [(kp[0], kp[1], kp[2]) for kp in keypoints]
        X_pred = extract_point_features(np_img, pts)
        if X_pred.shape[0] == len(pts):
            probs = model.predict_proba(X_pred)[:,1]
            # filter
            filtered = [kp for kp, p in zip(keypoints, probs) if p >= threshold]
            # keep also prob map for visualization
            keypoints = filtered
            st.sidebar.write(f"Nach Filter: {len(keypoints)} Kerne übrig (threshold {threshold})")
        else:
            st.sidebar.warning("Feature-Extraction hat ungewohnte Form — Model nicht angewendet.")

    # visualization
    vis = np.array(pil_img).copy()
    for (x,y,r) in keypoints:
        cv2.circle(vis, (x,y), int(round(r)), (255,0,0), 2)

    col1, col2 = st.columns(2)
    col1.image(pil_img, caption="Original", use_container_width=True)
    col2.image(vis, caption=f"Automatisch erkannte Kerne: {len(keypoints)}", use_container_width=True)

    # quick stats and allow saving params as example (for Stufe1.5)
    if st.button("Als Parameterbeispiel speichern (für Stufe1.5)"):
        features = {
            "contrast": float(cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY).std()),
            "mean_intensity": float(cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY).mean()),
            "shape": (orig_h, orig_w)
        }
        # append to parameter.csv
        df = pd.DataFrame([{
            "timestamp": time.time(),
            "name_pattern": getattr(uploaded, "name", "*"),
            "contrast": features["contrast"],
            "mean_intensity": features["mean_intensity"],
            "height": features["shape"][0],
            "width": features["shape"][1],
            "min_area": min_area,
            "max_area": max_area,
            "min_circularity": min_circularity,
            "min_inertia_ratio": min_inertia_ratio
        }])
        if not os.path.exists(PARAM_CSV):
            df.to_csv(PARAM_CSV, index=False)
        else:
            df.to_csv(PARAM_CSV, mode="a", header=False, index=False)
        st.success("Parameterbeispiel gespeichert in parameter.csv")

# ---------- Korrektur Tab ----------
with tabs[1]:
    st.header("✏️ Korrektur")
    # require uploaded image from Analyse tab
    if 'uploaded' not in locals():
        st.info("Bitte zuerst im Tab 'Analyse' ein Bild hochladen und erkennen.")
        st.stop()
    # re-run detection with current params
    pil_img = pil_open_rgb(uploaded)
    np_img = np.array(pil_img)
    orig_w, orig_h = pil_img.size

    # rerun detection
    keypoints = detect_nuclei_blobs(np_img, min_area, max_area, min_circularity, min_inertia_ratio)
    auto_centers = [(int(k[0]), int(k[1])) for k in keypoints]

    st.write(f"Automatisch erkannte Kerne: {len(auto_centers)}")

    # scale for canvas
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

    # preview
    preview = np.array(pil_for_canvas).copy()
    for (x,y) in auto_centers:
        px = int(round(x * (display_w / orig_w)))
        py = int(round(y * (display_h / orig_h)))
        cv2.circle(preview, (px,py), 6, (255,0,0), -1)
    st.image(preview, caption="Automatisch erkannte Punkte (rot)", use_container_width=True)

    st.markdown("**Interaktive Korrektur**: Oben grün = add, unten rot = remove.")
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

    added_pts = map_canvas_to_original(canvas_add.json_data if canvas_add else None, display_w, display_h, orig_w, orig_h)
    removed_pts = map_canvas_to_original(canvas_remove.json_data if canvas_remove else None, display_w, display_h, orig_w, orig_h)

    st.write(f"Hinzugefügt: {len(added_pts)} — Markiert zum Entfernen: {len(removed_pts)}")

    # combine
    final_pts = [p for p in auto_centers if not close_to_any(p, removed_pts, thr=12)]
    for a in added_pts:
        if not close_to_any(a, final_pts, thr=6):
            final_pts.append(a)

    # show final preview
    final_preview = np.array(pil_for_canvas).copy()
    for (x,y) in final_pts:
        px = int(round(x * (display_w / orig_w)))
        py = int(round(y * (display_h / orig_h)))
        cv2.circle(final_preview, (px,py), 6, (0,255,0), -1)
    st.image(final_preview, caption=f"Finale Punkte: {len(final_pts)}", use_container_width=True)

    # export and save feedback
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
        # save feedback
        if os.path.exists(FEEDBACK_JSON):
            with open(FEEDBACK_JSON, "r") as f:
                db = json.load(f)
        else:
            db = []
        db.append(entry)
        with open(FEEDBACK_JSON, "w") as f:
            json.dump(db, f, indent=2)
        st.success("Feedback gespeichert in feedback.json")

# ---------- Model-Train Tab ----------
with tabs[2]:
    st.header("⚙️ Modell-Training (Stufe 2)")
    st.write("Trainiere ein RandomForest aus dem gesammelten Feedback (benötigt scikit-learn).")

    st.write("Feedback-Einträge insgesamt:", (len(json.load(open(FEEDBACK_JSON))) if os.path.exists(FEEDBACK_JSON) else 0))

    if RandomForestClassifier is None:
        st.error("scikit-learn nicht installiert. Installiere: pip install scikit-learn joblib")
        st.stop()

    if st.button("Trainiere Modell jetzt"):
        X, y = build_training_data(FEEDBACK_JSON)
        if X is None or len(X) == 0:
            st.error("Nicht genug Trainingsdaten: es werden Bilder mit gespeicherten Korrekturen und die Originalbilddateien benötigt.")
        else:
            clf = train_and_save_model(X, y, MODEL_FILE)
            st.success(f"Modell trainiert und gespeichert als {MODEL_FILE}. Samples: {len(y)}")
            model = clf

    # show model status
    model = load_model()
    if model is not None:
        st.write("Modell vorhanden:", MODEL_FILE)
        st.write("Feature importances:", model.feature_importances_.tolist())
    else:
        st.info("Kein trainiertes Modell gefunden.")

st.caption("Hinweis: Für automatisches Training müssen die Originalbilddateien, die in feedback.json referenziert werden, lokal vorhanden sein, damit Feature-Extraktion möglich ist.")
