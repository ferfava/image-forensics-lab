"""Interfaz inicial; aún no contiene detector ni afirmaciones forenses."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from image_forensics.preprocessing.image_io import decode_rgb  # noqa: E402

st.set_page_config(page_title="Image Forensics Lab", page_icon="🔬", layout="wide")
st.title("🔬 Image Forensics Lab")
st.caption("Proyecto de investigación aplicada · Procesamiento de Imágenes · IFTS 18")
st.info("Versión inicial: carga y visualización de fotografías. El análisis se incorporará tras su evaluación.")
st.markdown("**Importante:** una anomalía visual no demuestra una manipulación digital.")
uploaded = st.file_uploader("Cargá una fotografía JPEG o PNG", type=["jpg", "jpeg", "png"])
if uploaded is not None:
    try:
        rgb = decode_rgb(uploaded.getvalue())
    except ValueError as error:
        st.error(str(error))
    else:
        st.image(rgb, caption=f"Imagen cargada · {rgb.shape[1]} × {rgb.shape[0]} px")
        st.success("Imagen validada. Los análisis estarán disponibles en próximos módulos.")
