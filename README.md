# Image Forensics Lab

Laboratorio educativo de análisis forense de imágenes digitales mediante procesamiento clásico y aprendizaje automático.

> **Estado:** estructura inicial. No existe todavía un detector entrenado ni una conclusión forense validada.

## Objetivo
Investigar si características extraídas con técnicas clásicas de procesamiento de imágenes ayudan a localizar regiones manipuladas mediante Random Forest y SVM, comparados con métodos clásicos de referencia.

## Alcance
1. Generar manipulaciones controladas y máscaras de referencia.
2. Implementar bordes, ruido, textura y mapas de diferencias por recompresión JPEG.
3. Extraer características por región y entrenar Random Forest y SVM.
4. Evaluar por fotografía original, con precisión, recall, F1 e IoU.
5. Publicar una aplicación interactiva en Streamlit.

**Limitación:** una anomalía no prueba que una foto haya sido manipulada. Uso académico, no certificación de autenticidad.

## Inicio rápido
Python 3.11 o 3.12:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m pytest -q
streamlit run app/main.py
```

## Estructura
- `app/`: interfaz Streamlit.
- `src/image_forensics/`: módulos de procesamiento, manipulación, características, detección y evaluación.
- `tests/`: pruebas automatizadas.
- `docs/`: protocolo y roadmap.
- `data/samples/`: imágenes de ejemplo (con licencias verificadas).
- `models/`: espacio reservado para modelos locales.

## Reproducibilidad y seguridad
- Separar entrenamiento, validación y prueba por fotografía original.
- Documentar semilla, versiones, parámetros y resultados.
- No publicar fotografías privadas, datasets, secretos ni modelos grandes.
- Procesar imágenes de usuarios temporalmente con límites de tamaño.

Ver [protocolo experimental](docs/experimental_protocol.md) y [roadmap](docs/roadmap.md).

**Proyecto final individual · Procesamiento de Imágenes · IFTS 18.**