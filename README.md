# Image Forensics Lab

Laboratorio académico de procesamiento y análisis exploratorio de imágenes digitales. Trabajo final individual · Procesamiento de Imágenes · IFTS 18.

> **Alcance científico:** la aplicación muestra características visuales y artefactos de procesamiento; no determina si una imagen es auténtica o falsa. No existe todavía un detector entrenado o validado.

## Arquitectura
- `frontend/`: interfaz web estática (HTML, CSS, JavaScript), alojable en Vercel.
- `backend/main.py`: API FastAPI, alojable en Render.
- `src/image_forensics/`: procesamiento reutilizable y validación de imágenes.
- `tests/`: pruebas automáticas.
- `docs/`: protocolo y plan de investigación.

## Funcionalidades
- Carga JPEG/PNG, máximo 12 MB y 16 megapíxeles.
- Detección de bordes Canny (umbrales 100/200).
- Histogramas RGB y en escala de grises.
- Suavizado gaussiano y filtro de mediana, más residuo visual.
- ELA (Error Level Analysis): recompresión JPEG con calidad 90, mapa de diferencias amplificado y error medio absoluto.

**Interpretación ELA:** regiones brillantes pueden corresponder a detalles, texturas, bordes, formatos previos o ediciones legítimas. No permiten concluir manipulación por sí solas. La escala de visualización varía con el máximo de diferencia de cada imagen y por ello el brillo no es directamente comparable entre fotografías.

## Ejecutar localmente
Requiere Python >=3.11:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
pip install -r requirements-dev.txt
python -m pytest -q
uvicorn backend.main:app --reload
```

Servir la carpeta `frontend/` con un servidor estático (por ejemplo, desde `frontend`: `python -m http.server 5500`). Editar `frontend/config.js` para apuntar a `http://localhost:8000` durante el desarrollo local. Configurar `CORS_ORIGINS` en el backend para el origen exacto del frontend.

## Trabajo pendiente
- Experimentar con textura, umbralización y morfología.
- Preparar fotografías con modificaciones controladas y máscaras de referencia.
- Extraer características por regiones, evaluar métodos clásicos y, si hay datos suficientes, Random Forest y SVM con división por fotografía original.
- Registrar métricas (precisión, recall, F1, IoU), limitaciones e informe académico.
- Validar despliegues, integración y pruebas antes de integrar a `main`.

Ver [protocolo](docs/experimental_protocol.md) y [roadmap](docs/roadmap.md).
