import streamlit as st
from PIL import Image, ImageDraw, ImageEnhance
import numpy as np

# 📁 Bild hochladen
uploaded_file = st.file_uploader("📁 Lade ein Bild hoch", type=["jpg", "jpeg", "png", "tif", "tiff"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")

    # 🎨 Farbkanal-Umschaltung
    kanal = st.selectbox("🎨 Farbkanal anzeigen", ["RGB", "Grau", "Rot", "Grün", "Blau"])

    # 🌓 Kontrastregler
    kontrast = st.slider("🌓 Kontrast", 0.5, 3.0, 1.0, 0.1)
    image = ImageEnhance.Contrast(image).enhance(kontrast)

    # 🖼️ Kanalansicht erzeugen
    image_np = np.array(image)
    if kanal == "Grau":
        image_show = Image.fromarray(np.array(image.convert("L")))
    elif kanal == "Rot":
        r = image_np[:, :, 0]
        image_show = Image.fromarray(np.stack([r, np.zeros_like(r), np.zeros_like(r)], axis=2).astype(np.uint8))
    elif kanal == "Grün":
        g = image_np[:, :, 1]
        image_show = Image.fromarray(np.stack([np.zeros_like(g), g, np.zeros_like(g)], axis=2).astype(np.uint8))
    elif kanal == "Blau":
        b = image_np[:, :, 2]
        image_show = Image.fromarray(np.stack([np.zeros_like(b), np.zeros_like(b), b], axis=2).astype(np.uint8))
    else:
        image_show = image

    st.image(image_show, caption=f"🖼️ Anzeige: {kanal}", use_column_width=True)

    # 🧪 Automatische Fleckenerkennung
    st.markdown("### 🧪 Automatische Fleckenerkennung")
    gray = np.array(image.convert("L"))
    threshold = st.slider("🎚️ Schwellenwert", 0, 255, 150)
    mask = gray < threshold
    coords = np.column_stack(np.where(mask))
    fleck_radius = st.slider("🔴 Fleckengröße", 5, 30, 10)

    image_auto = image.copy()
    draw_auto = ImageDraw.Draw(image_auto)
    for y, x in coords[::100]:  # Nur jeden 100. Punkt für Übersichtlichkeit
        draw_auto.ellipse((x - fleck_radius, y - fleck_radius, x + fleck_radius, y + fleck_radius), outline="blue")

    st.image(image_auto, caption="🔵 Automatisch erkannte Flecken", use_column_width=True)

    # ✏️ Manuelle Fleckenmarkierung
    st.markdown("### ✏️ Flecken manuell markieren")
    x = st.slider("X-Koordinate", 0, image.width, value=image.width // 2)
    y = st.slider("Y-Koordinate", 0, image.height, value=image.height // 2)

    image_manual = image_auto.copy()
    draw_manual = ImageDraw.Draw(image_manual)
    draw_manual.ellipse((x - 10, y - 10, x + 10, y + 10), fill="red")
    st.image(image_manual, caption="🟥 Manuell markierter Fleck", use_column_width=True)

    # 📦 Punktverwaltung
    if "punkte" not in st.session_state:
        st.session_state.punkte = []

    if st.button("📌 Punkt speichern"):
        st.session_state.punkte.append((x, y))
        st.success(f"Punkt gespeichert: ({x}, {y})")

    if st.session_state.punkte:
        st.markdown("### 📋 Gespeicherte Punkte")
        for idx, (px, py) in enumerate(st.session_state.punkte, 1):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{idx}. X: {px}, Y: {py}")
            with col2:
                if st.button(f"❌ Löschen {idx}", key=f"del_{idx}"):
                    st.session_state.punkte.pop(idx - 1)
                    st.experimental_rerun()

        st.markdown(f"**🔢 Gesamtzahl der Punkte:** {len(st.session_state.punkte)}")
