# Image Forensics Lab

Laboratorio académico de procesamiento y análisis exploratorio de imágenes digitales. Trabajo final individual · Procesamiento de Imágenes · IFTS 18.

> **Alcance científico:** la aplicación muestra características visuales y artefactos de procesamiento; no determina si una imagen es auténtica o falsa. Existen clasificadores experimentales entrenados localmente, pero ninguno está validado ni publicado como detector de autenticidad.

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

## Estado del proyecto y pendientes de entrega
- Implementados ELA, comparación controlada, histogramas, bordes y filtros.
- Realizados experimentos de clasificación sobre IMD2020 con Random Forest y SVM, incluyendo calibración y comparación V1/V2.
- El módulo ML sigue siendo exclusivamente experimental, sin validación externa ni acceso público desde el frontend.
- Pendiente: verificar despliegue frontend/backend desde Internet y preparar informe académico final; las métricas no certifican autenticidad.

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

Primer prototipo **local** con Random Forest y SVM. La entrada de inferencia es **una sola imagen**, sin referencia original. Extrae por parches de 32 × 32: intensidad y desviación estándar, Laplaciano, densidad de bordes, gradiente, variación RGB y residuo JPEG. Compara RF y SVM según F1 en validación, usando particiones separadas por fotografía de origen. Las posteriores inspecciones del conjunto de prueba impiden tratar sus métricas como un benchmark independiente definitivo.

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

## Incorporación de datasets externos

Fuentes candidatas (verificar las condiciones de uso antes de descargar):
- IMD2020: https://staff.utia.cas.cz/novozada/db/ (fotografías manipuladas reales, originales y máscaras).
- Image Forensics Dataset with Manipulation Masks: https://figshare.com/articles/dataset/Image_Forensics_Dataset_with_Manipulation_Masks/34603173 (CC BY 4.0 según la ficha del catálogo).

No se incluyen datos externos en el repositorio ni se descarga nada automáticamente.
Primero organizar en `data/real/` las imágenes y las máscaras binarias con rutas relativas en `manifest.csv`:
```csv
image,mask,group,source
images/001_editada.png,masks/001.png,original_001,dataset_ejemplo
```
Si hay imágenes auténticas sin modificaciones, usar una máscara **negra** del mismo tamaño y definir `group` según la fotografía de origen. Distintas versiones de una misma fotografía deben compartir `group`. Confirmar que las máscaras son blanco/negro con valores 0 y 255 y que marcan el área realmente editada.

Validar antes de entrenar:
```powershell
.\.venv\Scripts\python.exe -m image_forensics.detection.audit_dataset --manifest data/real/manifest.csv
.\.venv\Scripts\python.exe -m pytest tests/test_dataset_audit.py -v
```
El auditor verifica dimensiones, archivos faltantes, duplicados, rutas, máscaras no binarias y cantidad de grupos. **No comprueba licencias, independencia real entre imágenes ni calidad científica de las anotaciones**: requieren revisión humana. No entrenar si hay problemas.


### Importar IMD2020 desde sus carpetas originales

La estructura observada es `<caso>/<caso>_orig`, `<caso>/<id>_0`,
`<caso>/<id>_0_mask`. Un caso puede contener **múltiples manipulaciones**.
El importador mantiene el mismo `group` para todas las variantes del caso,
convierte las máscaras a blanco/negro estricto, incluye el original con máscara
negra y escribe `manifest_imd2020.csv` en la carpeta del dataset. No copia
fotografías al repositorio.

```powershell
.\.venv\Scripts\python.exe -m image_forensics.detection.import_imd2020 --root "C:\RUTA\A\IMD2020" --max-groups 30
.\.venv\Scripts\python.exe -m image_forensics.detection.audit_dataset --manifest "C:\RUTA\A\IMD2020\manifest_imd2020.csv"
.\.venv\Scripts\python.exe -m pytest tests/test_imd2020_import.py -v
```

Reemplazar la ruta por la carpeta extraída con las subcarpetas `1a1ogs`,
`1a3oag`, etc. Para el primer ensayo usar solo 30 casos; verificar
`warning_examples`, `ready` y la licencia del dataset antes de entrenar.
Las rutas se resuelven relativas al CSV: no mover el CSV solo.


## Diagnóstico por imagen y ampliación progresiva del dataset

Después del ensayo inicial de 30 grupos, ampliar a **60 grupos** (no a todas las
imágenes de golpe), usando el dataset extraído en Windows:

```powershell
.\.venv\Scripts\python.exe -m image_forensics.detection.import_imd2020 --root "C:\Users\Noxi-PC\Pictures\dataset" --max-groups 60
.\.venv\Scripts\python.exe -m image_forensics.detection.audit_dataset --manifest "C:\Users\Noxi-PC\Pictures\dataset\manifest_imd2020.csv"
.\.venv\Scripts\python.exe -m image_forensics.detection.train --manifest "C:\Users\Noxi-PC\Pictures\dataset\manifest_imd2020.csv" --out models/imd2020_60
```

**Importante:** el segundo importador reemplaza el CSV `manifest_imd2020.csv`,
pero no modifica las fotos ni el modelo antiguo guardado en `models/imd2020_30`.
Como la división train/validation/test se recalcula por grupos, **las métricas
de 30 y 60 grupos no son una comparación controlada**: cambia el conjunto de
prueba. Para comparar cambios de características/modelos, se debe fijar una
partición independiente de test y conservarla idéntica entre experimentos.

El entrenamiento ahora imprime el progreso de extracción cada cinco imágenes,
avisa al entrenar cada clasificador y crea en la carpeta de salida:

- `metrics.json`: métricas globales, distribución de parches por clase y split,
  resumen de fotografías de prueba con FP/FN.
- `test_by_image.csv`: una fila por fotografía en **test**, con grupo, ruta,
  positivos, TP/FP/FN/TN, precisión, recall y F1 de los parches.
- `model.joblib`: modelo experimental de origen local.

Para encontrar ejemplos problemáticos, ordenar el CSV por `fp` o `fn` de mayor
a menor. Los casos auténticos con máscara negra se incluyen en `test` para
medir falsas alarmas. Las métricas de las imágenes sin positivos se reportan
con `zero_division=0` y deben interpretarse según sus conteos, no como
fallos del modelo automáticamente.

Primero comprobar las pruebas:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```


## Etapa ML: calibración exploratoria y visualización de errores

A partir del dataset IMD2020 auditado con **60 grupos**:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m image_forensics.detection.calibrate --manifest "C:\Users\Noxi-PC\Pictures\dataset\manifest_imd2020.csv" --out models/imd2020_60_calibrated
```

El proceso vuelve a extraer características y **entrena un SVM nuevo**. No se
sobrescribe el resultado anterior `models/imd2020_60`. Muestra progreso cada
cinco imágenes.

Resultados en `models/imd2020_60_calibrated/`:

- `split.json`: asignación fija de grupos train/validation/test y SHA256 del
  manifiesto. Rechaza reutilizar la partición si el CSV cambia.
- `calibration_report.json`: criterio **F0.5** elegido de antemano para dar
  más importancia a precisión que a recall, umbral calibrado *solo con
  validación*, distribución y tres comparadores en el mismo test (clasificar
  todo normal, SVM umbral 0, SVM calibrado).
- `test_by_image_calibrated.csv`: errores por fotografía de test.
- `error_maps/*.png`: cuatro fotografías de test con mayores falsos
  positivos, a la izquierda imagen, a la derecha superposición: **verde TP,
  rojo FP, azul FN** (por píxel a partir de bloques de 32; no es
  segmentación de precisión fina).
- `calibrated_model.joblib`: modelo que la inferencia local puede usar.

Ejemplo de análisis de una sola imagen (sin imagen original):
```powershell
.\.venv\Scripts\python.exe -m image_forensics.detection.infer --model models/imd2020_60_calibrated/calibrated_model.joblib --image "C:\RUTA\imagen.jpg" --out outputs/ml_suspect_mask.png
```

**Nota científica esencial:** los datos de test de IMD2020_60 ya se analizaron
en experimentos previos, por lo que **NO SON un test final intocado**.
La calibración usa únicamente validación, pero el análisis completo todavía
es exploratorio. Antes de publicar afirmaciones de rendimiento o desplegar un
detector se necesitará reservar nuevas fotografías no consultadas, fijar una
partición de evaluación final y estimar incertidumbre. Un mejor F0.5 puede
reducir falsos positivos y también reducir el recall: comparar ambos conteos.

El modelo no determina si una fotografía es auténtica o falsa.


## Experimento V2: textura LBP y comparación local

Se conserva la **V1 de 8 características** y se agrega V2 con **14
características**. Las seis nuevas incluyen dos estadísticas de Local Binary
Patterns (uniformidad energética y entropía) y cuatro contrastes contra
los parches vecinos de la misma foto (media de grises, desviación de grises,
residuo JPEG y entropía LBP). La comparación es espacial y no requiere
imagen original durante inferencia.

**La única comparación controlada aceptada** debe usar el split bloqueado de
la calibración anterior; si falta `split.json`, el script no inventa uno.

```powershell
git pull --ff-only origin feature/jpeg-ela-analysis
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m image_forensics.detection.compare_v2 --manifest "C:\Users\Noxi-PC\Pictures\dataset\manifest_imd2020.csv" --split models/imd2020_60_calibrated/split.json --out models/imd2020_v1_v2
```

El entrenamiento V1 y V2 puede consumir CPU por la SVM; muestra progreso
de extracción cada cinco fotos y después el resultado de ambos modelos.
Produce `models/imd2020_v1_v2/comparison_v1_v2.json`,
`v1_model.joblib` y `v2_model.joblib` sin sobrescribir resultados previos.
Para inferencia local en una sola fotografía también funciona el artefacto
V2 con `image_forensics.detection.infer`.

Ambos SVM usan los mismos hiperparámetros y seleccionan su umbral en
**validación** optimizando F0.5. La comparación emplea idéntico
conjunto de prueba y etiquetas por parche. No se selecciona un modelo final
mirando el resultado de test. **Los grupos de prueba ya fueron revisados en
ensayos anteriores**: este resultado es exploratorio y será necesario
reservar un conjunto nuevo nunca visto para el informe de generalización.
El script no afirma que V2 vaya a mejorar los indicadores.
