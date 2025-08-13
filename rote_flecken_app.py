import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import numpy as np

st.title("🖌 Interaktive Marker direkt auf Bild – nur Umrandung")

# ------------------------
# Bild-Upload
# ------------------------
uploaded_file = st.sidebar.file_uploader("Bild auswählen", type=["png","jpg","jpeg"])
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(img)
    height, width = img_np.shape[:2]

    # ------------------------
    # Kreis-Parameter
    # ------------------------
    radius = st.sidebar.slider("Kreis-Radius in Pixel", 5, 100, 20)
    circle_color = st.sidebar.color_picker("Farbe Kreis-Umrandung", "#00FF00")
    poly_color = st.sidebar.color_picker("Farbe Polygon", "#FF0000")

    # ------------------------
    # Session State
    # ------------------------
    if "circles" not in st.session_state:
        st.session_state.circles = []  # (x, y)
    if "polygons" not in st.session_state:
        st.session_state.polygons = []  # Liste von Polygonen
    if "current_poly" not in st.session_state:
        st.session_state.current_poly = []

    # ------------------------
    # Plotly Figure erstellen
    # ------------------------
    fig = px.imshow(img_np)
    fig.update_layout(
        dragmode="drawopenpath",  # für Mausinteraktion
        newshape=dict(line_color=poly_color, fillcolor='rgba(0,0,0,0)'),
        margin=dict(l=0,r=0,t=0,b=0),
        width=width,
        height=height
    )

    # Kreise zeichnen
    for x, y in st.session_state.circles:
        fig.add_shape(
            type="circle",
            x0=x-radius, y0=y-radius,
            x1=x+radius, y1=y+radius,
            line=dict(color=circle_color, width=2),
        )

    # Polygone zeichnen
    for poly in st.session_state.polygons:
        x_coords, y_coords = zip(*poly)
        fig.add_trace(go.Scatter(x=x_coords + (x_coords[0],), y=y_coords + (y_coords[0],),
                                 mode="lines", line=dict(color=poly_color, width=2), fill='none'))

    st.plotly_chart(fig)

    st.write(f"Anzahl Kreise: {len(st.session_state.circles)}")
    st.write(f"Anzahl Polygone: {len(st.session_state.polygons)}")
