import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
from sklearn.cluster import DBSCAN

# Dummy-Bild erzeugen
image = Image.new("RGB", (600, 400), "white")
draw = ImageDraw.Draw(image)

# Beispielpunkte (automatisch erkannte + manuelle)
coords = np.random.randint(50, 550, size=(100, 2))
if "punkte" not in st.session_state:
    st.session_state.punkte = []

# Layout: Bild links, Regler rechts
col_img, col_ctrl = st.columns([3, 1])
with col_ctrl:
    kontrast = st.slider("🌓 Kontrast", 0.5, 3.0, 1.0, 0.1)
    radius = st.slider("📏 Markierungsradius", 5, 30, 10)
    threshold = st.slider("🎚️ Schwellenwert (Helligkeit)", 0, 255, 100)
    gruppen_radius = st.slider("📏 Gruppierungsradius", 10, 100, 30)

# Punkte kombinieren
all_coords = np.array(st.session_state.punkte + list(coords))

# Gruppierung mit DBSCAN
clustering = DBSCAN(eps=gruppen_radius, min_samples=1).fit(all_coords)
labels = clustering.labels_
unique_groups = len(set(labels))

# Farben für Gruppen
farben_gruppen = ["red", "green", "blue", "orange", "purple", "cyan", "magenta", "yellow"]

# Gruppen zeichnen
for group_id in set(labels):
    group_points = all_coords[labels == group_id]
    for x, y in group_points:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=farben_gruppen[group_id % len(farben_gruppen)])

# Anzeige
with col_img:
    st.image(image, caption="🖼️ Bild mit Fleckengruppen", use_column_width=True)

with col_ctrl:
    st.metric("🧮 Gruppenanzahl", unique_groups)
