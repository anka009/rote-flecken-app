import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from sklearn.cluster import DBSCAN

st.set_page_config(layout="wide")
st.title("🩸 Rote Flecken Gruppierung")

# 📤 Bild-Upload
uploaded_file = st.file_uploader("Bild hochladen", type=["jpg", "png", "jpeg"])
if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Dummy-Erkennung (ersetzen durch echte Analyse)
    coords = np.random.randint(50, min(image.size)-50, size=(100, 2))

    if "punkte" not in st.session_state:
        st.session_state.punkte = []

    # 📐 Layout: Bild links, Regler rechts
    col_img, col_ctrl = st.columns([3, 1])
    with col_ctrl:
        radius = st.slider("📏 Markierungsradius", 5, 30, 10)
        gruppen_radius = st.slider("📏 Gruppierungsradius", 10, 100, 30)

    # 🔄 Punkte kombinieren
    all_coords = np.array(st.session_state.punkte + list(coords))

    # 🧠 Gruppierung
    clustering = DBSCAN(eps=gruppen_radius, min_samples=1).fit(all_coords)
    labels = clustering.labels_
    unique_groups = len(set(labels))

    # 🖍️ Gruppen umrahmen
    for group_id in set(labels):
        group_points = all_coords[labels == group_id]
        if len(group_points) > 1:
            x_mean = int(np.mean(group_points[:, 0]))
            y_mean = int(np.mean(group_points[:, 1]))
            r_group = int(np.max(np.linalg.norm(group_points - [x_mean, y_mean], axis=1))) + radius
            draw.ellipse((x_mean - r_group, y_mean - r_group, x_mean + r_group, y_mean + r_group),
                         outline="red", width=2)

    # 🔘 Einzelpunkte markieren
    for x, y in all_coords:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="black", width=1)

    # 📊 Anzeige
    with col_img:
        st.image(image, caption="🖼️ Gruppierte Flecken", use_column_width=True)
    with col_ctrl:
        st.metric("🧮 Gruppenanzahl", unique_groups)
else:
    st.warning("Bitte lade ein Bild hoch, um die Flecken zu analysieren.")
