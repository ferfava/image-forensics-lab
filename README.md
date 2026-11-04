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
- Evaluación opcional de la máscara detectada frente a una máscara de referencia conocida: precisión, recall, F1, IoU y TP/FP/FN/TN.

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
- Validar con un dataset real la extracción por regiones, Random Forest y SVM ya implementados como prototipo experimental.
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

## Evaluación experimental con máscara de referencia

En `/api/compare`, el tercer archivo `ground_truth` es opcional: PNG/JPEG en blanco y negro, con **las mismas dimensiones** que las dos fotos. Blanco (luminancia >=128) = región realmente modificada; negro = resto. Los cálculos se hacen antes de reducir las imágenes para visualización.

Se comparan los píxeles marcados por la máscara detectada (máxima diferencia de canales RGB >20) con los de la máscara de referencia. Se presentan:
- **Precisión:** TP/(TP+FP), entre los marcados, cuántos corresponden a la región anotada.
- **Recall:** TP/(TP+FN), qué porcentaje de la región anotada fue recuperado.
- **F1:** 2TP/(2TP+FP+FN).
- **IoU:** TP/(TP+FP+FN).

Si ambas máscaras están vacías se devuelve 1.0 por coincidencia perfecta, acompañado del indicador `empty_case=true`. Un valor alto mide coincidencia frente a la máscara suministrada, **no certificación de autenticidad**. Las máscaras de referencia deben delinearse a partir de la edición conocida, no a partir de la predicción, para evitar una evaluación circular.

## ML experimental (sin desplegar al público)

Primer prototipo **local** con Random Forest y SVM. La entrada de inferencia es **una sola imagen**, sin referencia original. Extrae por parches de 32 × 32: intensidad y desviación estándar, Laplaciano, densidad de bordes, gradiente, variación RGB y residuo JPEG. Elige entre RF y SVM según F1 en validación; reporta métricas finales una sola vez sobre test no visto, separado por fotografía de origen.

En PowerShell desde la raíz:
```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m image_forensics.detection.synthetic_data --out data/ml_synthetic
.\.venv\Scripts\python.exe -m image_forensics.detection.train --manifest data/ml_synthetic/manifest.csv --out models/experimental
.\.venv\Scripts\python.exe -m pytest tests/test_ml_pipeline.py -v
.\.venv\Scripts\python.exe -m image_forensics.detection.infer --model models/experimental/model.joblib --image data/ml_synthetic/images/sample_001.png --out outputs/ml_mask.png
```

Se generan `models/experimental/model.joblib` y `models/experimental/metrics.json`. Los archivos `data/`, `models/` y archivos locales de prueba no se suben al repositorio. **No cargar modelos .joblib de terceros desconocidos.**

El dataset sintético es únicamente una **prueba técnica del pipeline**. Sus resultados no sirven para demostrar que el modelo detecta fotos trucadas reales. Se requieren fotografías reales y editadas de diversas fuentes, máscaras independientes, partición por original, análisis por tipo de edición, IoU por píxel e intervalos de incertidumbre. Parches de borde incompletos se omiten; la máscara de inferencia tiene resolución de bloques, no contornos de precisión fina.

### Manifest para un dataset real

Archivo CSV UTF-8 con columnas `image,mask,group,source`, rutas relativas al CSV, por ejemplo:
```csv
image,mask,group,source
images/foto1_editada.png,masks/foto1_editada.png,foto1,edicion_controlada
images/foto1_otra_edicion.png,masks/foto1_otra_edicion.png,foto1,edicion_controlada
images/foto2.png,masks/foto2.png,foto2,edicion_controlada
```
Todas las derivaciones de una fotografía original deben llevar el mismo identificador `group`, incluso si son distintas modificaciones.
