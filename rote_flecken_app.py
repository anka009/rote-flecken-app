import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import numpy as np
import io

st.set_page_config(page_title="Interaktiver Objekte-Zähler", layout="wide")
st.title("🖌️ Interaktiver Objekte-Zähler")

uploaded_file = st.file_uploader(
    "Bild hochladen (PNG, JPG, JPEG, TIFF/TIF)",
    type=["png", "jpg", "jpeg", "tif", "tiff"]
)

if uploaded_file:
    # PIL Bild laden
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)

    # PNG Bytes erstellen für Canvas
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    st.sidebar.header("Einstellungen für Markierung")
    circle_radius = st.sidebar.slider("Radius der Markierungen (px)", 5, 50, 15)
    circle_color = st.sidebar.color_picker("Farbe der Markierung", "#00FF00")
    line_width = st.sidebar.slider("Linienstärke", 1, 10, 2)

    st.subheader("Markiere die Objekte")

    # Canvas mit PNG-Bytes als Hintergrund
    canvas_result = st_canvas(
        fill_color="",  
        stroke_width=line_width,
        stroke_color=circle_color,
        background_image=Image.open(io.BytesIO(img_bytes)),
        update_streamlit=True,
        height=img_np.shape[0],
        width=img_np.shape[1],
        drawing_mode="circle",
        key="canvas"
    )

    # Objekte zählen
    count = 0
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        count = len(objects)

    st.markdown(f"### Anzahl markierter Objekte: **{count}**")

    # CSV Download
    import csv
    if count > 0:
        csv_buf = io.StringIO()
        writer = csv.writer(csv_buf)
        writer.writerow(["X", "Y", "Radius"])
        for obj in objects:
            if obj["type"] == "circle":
                x = obj["left"] + obj["radius"]
                y = obj["top"] + obj["radius"]
                r = obj["radius"]
                writer.writerow([x, y, r])
        st.download_button(
            "📥 Markierungen als CSV herunterladen",
            data=csv_buf.getvalue(),
            file_name="markierungen.csv",
            mime="text/csv"
        )
