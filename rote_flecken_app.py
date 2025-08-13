import streamlit as st
from PIL import Image
import numpy as np
import io
import csv

# ---------------- Helpers -----------------
def points_to_csv_bytes(points):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["x", "y"])
    for x, y in points:
        writer.writerow([x, y])
    return buf.getvalue().encode("utf-8")

def draw_points_on_image(img, points, radius=10, color=(255,0,0)):
    img_copy = img.copy()
    for x, y in points:
        # PIL ellipse expects (left, top, right, bottom)
        img_copy_draw = Image.fromarray(np.array(img_copy))
        img_copy_draw = img_copy
        # Draw circle
        img_copy_draw = img_copy_draw.convert("RGB")
        import cv2
        img_np = np.array(img_copy_draw)
        cv2.circle(img_np, (x, y), radius, color, 2)
        img_copy = Image.fromarray(img_np)
    return img_copy

# ---------------- Streamlit UI -----------------
st.set_page_config(page_title="🖌️ Interaktiver Objekte-Zähler", layout="wide")
st.title("🖌️ Interaktiver Objekte-Zähler")

# Upload
uploaded_file = st.file_uploader("Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)", type=["png","jpg","jpeg","tif","tiff"])
if not uploaded_file:
    st.info("Bitte zuerst ein Bild hochladen.")
    st.stop()

# Bild laden (TIFF -> RGB)
img = Image.open(uploaded_file)
if img.mode != "RGB":
    img = img.convert("RGB")
width, height = img.size

# Session state
if "points" not in st.session_state:
    st.session_state.points = []

st.sidebar.header("Markierungseinstellungen")
radius = st.sidebar.slider("Radius der Markierungen (px)", 2, 50, 10)
color = st.sidebar.color_picker("Farbe der Markierungen", "#ff0000")
line_thickness = st.sidebar.slider("Linienstärke", 1, 10, 2)

st.markdown(f"**Anzahl markierter Objekte:** {len(st.session_state.points)}")

# Canvas-Klicks simulieren mit streamlit_image_coordinates
try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    coords = streamlit_image_coordinates(img, key="img_coords")
    if coords:
        x, y = coords["x"], coords["y"]
        # Prüfen, ob Klick in bestehendem Punkt -> löschen
        removed = False
        for i, (px, py) in enumerate(st.session_state.points):
            if (px - x)**2 + (py - y)**2 <= radius**2:
                st.session_state.points.pop(i)
                removed = True
                st.success(f"Punkt bei ({px},{py}) gelöscht.")
                break
        if not removed:
            st.session_state.points.append((x, y))
            st.success(f"Punkt bei ({x},{y}) hinzugefügt.")
except Exception:
    st.warning("streamlit_image_coordinates nicht installiert. Benutze manuelle Controls.")
    col1, col2 = st.columns(2)
    with col1:
        new_x = st.number_input("X hinzufügen", 0, width-1, step=1)
        new_y = st.number_input("Y hinzufügen", 0, height-1, step=1)
        if st.button("Punkt hinzufügen"):
            st.session_state.points.append((new_x, new_y))
    with col2:
        if st.session_state.points:
            idx = st.selectbox("Punkt auswählen zum Entfernen", list(range(len(st.session_state.points))))
            if st.button("Ausgewählten Punkt entfernen"):
                removed = st.session_state.points.pop(idx)
                st.info(f"Punkt {removed} entfernt.")

# Bild mit Punkten anzeigen
marked_img = draw_points_on_image(img, st.session_state.points, radius=radius, color=tuple(int(color.lstrip("#")[i:i+2],16) for i in (0,2,4)))
st.image(marked_img, caption="Markierte Objekte", use_column_width=True)

# CSV Export
if st.session_state.points:
    csv_bytes = points_to_csv_bytes(st.session_state.points)
    st.download_button("📥 Punkte als CSV herunterladen", data=csv_bytes, file_name="points.csv", mime="text/csv")
