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
- ELA (Error Level Analysis): recompresión JPEG con calidad 90, mapa de diferencias sin amplificar, control de contraste visual y error medio absoluto.
- Comparador de dos imágenes: mapa absoluto RGB ×4 visual, máscara de cambios por píxel con umbral >20, diferencia media absoluta y porcentaje de píxeles sobre umbral.

**Interpretación ELA:** regiones brillantes pueden corresponder a detalles, texturas, bordes, formatos previos o ediciones legítimas. No permiten concluir manipulación por sí solas. El control de amplificación (×1 a ×64) permite inspeccionar el mapa sin alterar los datos ni la métrica. Para comparar imágenes hay que usar la misma calidad y la misma amplificación; aun así los mapas no son una prueba de autenticidad.

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

## Protocolo breve de prueba comparativa
1. Elegir una imagen que podamos modificar y guardar una copia intacta.
2. Registrar formato, dimensiones y tamaño; analizar la copia original.
3. Modificar una región de manera controlada y exportar la versión editada con las mismas dimensiones y un procedimiento de guardado documentado.
4. Analizar ambas con JPEG calidad 90 y el mismo factor de amplificación; anotar diferencia media y observaciones.
5. Evitar interpretar mayor brillo como manipulación demostrada; la recompresión anterior y las texturas son variables de confusión.

**Desarrollo local:** `frontend/config.js` debe apuntar a `http://127.0.0.1:8000` al usar el backend local. No subir ese cambio de configuración si el despliegue público sigue usando Render.

## Comparador experimental (/api/compare)

1. Cargar dos imágenes JPEG o PNG (cada una hasta 12 MB, 16 megapíxeles como máximo).
2. La API exige idénticas dimensiones tras corregir orientación EXIF. No redimensiona ni alinea las entradas para calcular.
3. Diferencia media absoluta (MAE): promedio de |RGB A − RGB B| por canal, rango 0–255.
4. Máscara: un píxel se marca si **algún** canal tiene diferencia absoluta mayor que 20.
5. Porcentaje: píxeles marcados dividido por el total de píxeles; no es porcentaje de falsificación.
6. Los mapas mostrados pueden reducirse para visualizarse; las métricas siempre se calculan a resolución completa.

**Limitaciones:** diferencias de iluminación, compresión, color, exportación o desalineación generan cambios incluso sin manipulación maliciosa. Para pruebas controladas, partir de una copia idéntica y modificar una región conocida, manteniendo el mismo tamaño.
