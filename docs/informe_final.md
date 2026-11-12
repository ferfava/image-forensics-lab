# Image Forensics Lab
## Informe técnico de cierre — Procesamiento de Imágenes

**Autora:** Fernanda Andrea Fava  
**Institución:** IFTS N.º 18  
**Asignatura:** Procesamiento de Imágenes  
**Fecha:** noviembre de 2026  
**Estado:** prototipo web funcional; detección automática con aprendizaje automático **EXPERIMENTAL_NO_VALIDADO**.

## Resumen

Image Forensics Lab es un laboratorio web que permite estudiar fotografías mediante técnicas clásicas de procesamiento digital: detección de bordes, histogramas, filtros, residuos de suavizado y análisis de recompresión JPEG (ELA). También permite comparar dos imágenes de iguales dimensiones, obtener una máscara de cambios y, si se dispone de una máscara de referencia independiente, calcular métricas de localización.

Como línea experimental adicional, se implementó una clasificación supervisada de regiones de 32 × 32 píxeles en imágenes individuales. Se evaluaron Random Forest y SVM, y dos representaciones SVM con ocho (V1) y catorce (V2) características. Los resultados demostraron una elevada cantidad de falsos positivos: el modelo **no** constituye una herramienta validada para certificar autenticidad.

## 1. Problema y objetivos

**Pregunta de investigación:** ¿qué información aportan las técnicas clásicas para visualizar cambios en imágenes y hasta qué punto esas características permiten localizar modificaciones sin disponer de una fotografía original?

Objetivos específicos:
1. Implementar un frontend académico reproducible para explorar características visuales.
2. Analizar bordes, distribución tonal, suavizado y recompresión JPEG.
3. Comparar imágenes controladas y medir la coincidencia con anotaciones independientes.
4. Construir un prototipo de aprendizaje supervisado por parche y evaluar sus errores.
5. Documentar las limitaciones y evitar inferencias injustificadas sobre autenticidad.

Se diferencian dos escenarios: **comparación asistida con imagen de referencia** (aplicación web) y **predicción sobre una sola imagen** (ML experimental). Son problemas distintos y sus métricas no deben mezclarse.

## 2. Arquitectura y tecnologías

- **Frontend:** HTML, CSS y JavaScript; desplegado en Vercel.
- **Backend:** Python, FastAPI y OpenCV; API pública desplegada en Render.
- **Procesamiento:** NumPy, OpenCV y Pillow.
- **Aprendizaje supervisado:** scikit-learn, StandardScaler, RandomForestClassifier y SVC (kernel RBF).
- **Ensayos reproducibles:** pytest; repositorio GitHub con código, pruebas y documentación.

La aplicación recibe fotografías JPEG/PNG de hasta 12 MB y valida un límite de 16 megapíxeles. La API no almacena las imágenes de las solicitudes. La inferencia del SVM V1 funciona tanto localmente como en el servicio público, mediante un artefacto numérico NPZ exportado del modelo original.

### 2.1 Estado del despliegue público (noviembre de 2026)

El frontend de Vercel consume la API FastAPI de Render. El clasificador V1 se distribuye como
`backend/assets/svm_v1.npz` (no como un archivo pickle): contiene coeficientes
y vectores de soporte del SVM RBF y se cargó con `allow_pickle=False`.
La exportación se verificó frente al modelo original con diferencia máxima en
puntuaciones de aproximadamente **4,1 × 10⁻¹⁰** (comprobación numérica, **no**
de precisión de detección). Las **40 pruebas automáticas** pasaron en el equipo
de desarrollo antes de la publicación. Una demostración pública real generó
superposición y máscara por parches; sobre el ejemplo sintético de escritorio,
el modelo señaló **36,46 % de la superficie**, lo cual **no** representa el
porcentaje realmente modificado ni una probabilidad de falsificación.

Se incluyen tres escenas sintéticas controladas generadas en el frontend
(costa, escritorio y ciudad), cada una con original, editada y máscara de
referencia. Sirven para ilustrar el flujo del laboratorio, **no** forman parte
del entrenamiento y **no** validan el SVM en fotografías reales.

## 3. Técnicas clásicas implementadas

### 3.1 Bordes Canny
Se convierte la imagen a escala de grises y se ejecuta `cv2.Canny` con umbrales 100 y 200. Resalta cambios pronunciados de intensidad, pero los bordes no representan por sí mismos evidencias de edición.

### 3.2 Histogramas
Se calculan distribuciones de intensidad de 256 niveles para los canales rojo, verde, azul y la imagen gris. Sirven para describir características tonales sin implicar falsificación.

### 3.3 Filtrado
Se aplica desenfoque gaussiano 5×5 y filtro de mediana 5×5. El residuo es la diferencia absoluta entre la imagen y su versión gaussiana; la interfaz lo amplifica ×4 **solo para visualizarlo**.

### 3.4 ELA — Error Level Analysis
Se recomprime la fotografía a JPEG de calidad 90 y se calcula un mapa de diferencias. El frontend permite amplificar su contraste sin alterar el error absoluto medio calculado. Las diferencias pueden deberse a textura, bordes, compresión previa, exportaciones o edición legítima: **ELA no certifica manipulaciones**.

### 3.5 Comparación controlada de dos fotografías
La referencia y la candidata deben tener las mismas dimensiones. Se calcula diferencia absoluta RGB y se marca un píxel cuando **algún canal** supera una diferencia de 20 niveles. El mapa absoluto se amplifica ×4 para su visualización, pero las métricas usan los píxeles originales. Opcionalmente se suministra una máscara de referencia blanco/negro; el backend calcula precisión, recall, F1, IoU y TP/FP/FN/TN sobre **píxeles**.

Esta comparación puede identificar diferencias entre archivos, pero no determinar la intención o causa del cambio. El experimento requiere conservar una referencia y registrar el procedimiento de edición y exportación.

## 4. Diseño del experimento ML

### 4.1 Datos y unidades
Se utilizó una muestra local de **251 imágenes de IMD2020**, agrupadas en **60 fotografías de origen**. Se extrajeron **246.699 parches no solapados de 32×32 píxeles**. El conjunto contiene originales, versiones modificadas y máscaras de anotación, que no se incluyen en GitHub.

La etiqueta del parche es positiva si **al menos 10 %** de sus píxeles están marcados como modificados en la máscara. Este criterio simplifica la anotación pero introduce ambigüedad en los bordes de las regiones alteradas.

### 4.2 Separación y prevención de fugas
Se usó partición agrupada por fotografía de origen: **36 grupos de entrenamiento, 12 de validación y 12 de prueba**. Todas las variantes de un mismo origen se mantienen en la misma partición. El archivo local `split.json` conserva las asignaciones y la huella SHA256 del manifiesto.

En la comparación V1/V2 se utilizó **exactamente el mismo split**, con 52.754 parches en prueba, de los cuales 3.489 tenían etiqueta positiva. Los datos se estandarizaron en un pipeline `StandardScaler + SVC` para evitar ajustar la escala con los datos de prueba.

### 4.3 Características
**V1 (8 variables):** media y desviación de grises; varianza del Laplaciano; densidad de bordes Canny; magnitud media del gradiente; desviación estándar RGB por canal promediada; media y desviación del residuo de recompresión JPEG.

**V2 (14 variables):** las ocho anteriores y seis adicionales: uniformidad/energía y entropía de códigos Local Binary Patterns (LBP), y diferencias absolutas respecto de la mediana de parches vecinos para media de grises, desviación de grises, residuo JPEG medio y entropía LBP.

Los dos SVM utilizan `kernel="rbf"`, `C=1`, `gamma="scale"` y `class_weight="balanced"`. Se calibra la puntuación de decisión con un umbral elegido **solo en validación**, maximizando F0.5 (mayor énfasis en precisión). Esa puntuación no representa una probabilidad de falsificación.

## 5. Resultados experimentales

### 5.1 Efecto de calibrar el SVM V1
Resultados de la ejecución de calibración sobre el mismo conjunto de prueba:

| Métrica por parche | SVM umbral 0 | SVM calibrado |
|---|---:|---:|
| Precisión | 11,97 % | 15,28 % |
| Recall | 50,36 % | 26,14 % |
| F1 | 19,34 % | 19,28 % |
| Verdaderos positivos | 1.757 | 912 |
| Falsos positivos | 12.926 | 5.058 |
| Falsos negativos | 1.732 | 2.577 |

El umbral seleccionado fue aproximadamente **0,8294**. Las falsas alarmas se redujeron un **60,9 %**, pero se detectaron menos alteraciones. No hubo una mejora material del F1. Se registraron mapas visuales de errores con verde = TP, rojo = FP y azul = FN, superpuestos sobre las imágenes.

### 5.2 Comparación controlada V1 frente a V2
En una ejecución posterior se reentrenaron ambos modelos en el mismo split. Los valores de V1 difieren mínimamente de la calibración anterior por la selección del umbral candidato.

| Métrica por parche | V1: 8 características | V2: 14 características |
|---|---:|---:|
| Precisión | **15,27 %** | 13,22 % |
| Recall | 26,17 % | **29,78 %** |
| F1 | **19,29 %** | 18,31 % |
| Verdaderos positivos | 913 | 1.039 |
| Falsos positivos | **5.066** | 6.822 |
| Falsos negativos | 2.576 | **2.450** |
| F0.5 en validación | **0,3164** | 0,2930 |

V2 recuperó **126 parches positivos más**, pero agregó **1.756 falsos positivos** (+34,7 %). La adición de características **no demostró una mejora global** bajo esta configuración. V1 se conserva como referencia exploratoria; V2 como resultado negativo documentado.

### 5.3 Diagnóstico cualitativo
En mapas de error se observaron falsas alarmas sobre pelaje, plumas, contornos, números grandes y fondos luminosos. Esto sugiere —sin demostrar causalidad por sí solo— que los descriptores responden a bordes y texturas naturales que se parecen a señales de modificación.

## 6. Validación técnica y limitaciones

La última suite de pruebas informada por ejecución local finalizó con **35 pruebas aprobadas** (`35 passed in 6.57s`) antes de los últimos cambios de interfaz y documentación. Las pruebas verifican componentes del procesamiento y de la canalización ML; no constituyen una validación de rendimiento forense.

Limitaciones relevantes:

1. El dataset de 60 grupos se ha inspeccionado durante el desarrollo; por eso **la prueba no es un benchmark final independiente** y no permite afirmar generalización.
2. Las métricas ML son **por parche**, no métricas de segmentación precisas por píxel. La visualización proyecta bloques y puede generar errores de borde.
3. Los parches no solapados no cubren necesariamente los restos de imagen que no completan 32 píxeles.
4. El desbalance de clases y la heterogeneidad de compresión y contenido afectan la precisión; `class_weight="balanced"` no los resuelve por completo.
5. ELA, residuos, mapas de bordes y diferencias no distinguen automáticamente ediciones fraudulentas de cambios legítimos.
6. No se evaluó detección general de imágenes generadas por inteligencia artificial.
7. Las condiciones de uso y atribución de los datos externos deben cotejarse con las fuentes antes de distribuir imágenes o incorporarlas al informe.

## 7. Conclusiones

El proyecto logró un laboratorio web funcional para explorar y comparar características de imágenes digitales con procedimientos reproducibles. La comparación controlada ofrece métricas espaciales cuando existe una referencia independiente; la detección automática sin referencia sigue siendo un problema considerablemente más difícil.

La experimentación ML fue informativa incluso sin conseguir un detector fiable: la calibración mostró el compromiso entre reducción de falsas alarmas y pérdidas de detección; la ampliación de características V2 incrementó el recall pero perjudicó precisión y F1. El resultado demuestra la importancia de medir y examinar los errores, no solo producir predicciones.

**Alcance final defendible:** laboratorio académico de procesamiento y análisis exploratorio de imágenes, más un módulo de investigación ML local **no validado**. La herramienta **no certifica autenticidad**.

## 8. Reproducción y archivos relevantes

- Aplicación: https://image-forensics-lab-frontend.vercel.app/
- Código: https://github.com/ferfava/image-forensics-lab
- Backend: `backend/main.py`; frontend: `frontend/`.
- Extracción: `src/image_forensics/features/patches.py` y `patches_v2.py`.
- Entrenamiento: `src/image_forensics/detection/train.py`.
- Calibración: `src/image_forensics/detection/calibrate.py`.
- Comparación: `src/image_forensics/detection/compare_v2.py`.
- Pruebas: `tests/`.

Artefactos de las ejecuciones locales (no versionados): `models/imd2020_60_calibrated/calibration_report.json`, `error_maps/*.png`, `models/imd2020_v1_v2/comparison_v1_v2.json`, `split.json` y los modelos `.joblib`. Para reproducirlos se necesita disponer del dataset de origen y del manifiesto local correspondiente.

## 9. Fuentes de referencia para completar bibliografía formal

- Documentación de OpenCV: https://docs.opencv.org/
- Documentación de scikit-learn: https://scikit-learn.org/stable/
- Dataset IMD2020, sitio de referencia mencionado en el proyecto: https://staff.utia.cas.cz/novozada/db/
- Documentación de FastAPI: https://fastapi.tiangolo.com/

**Nota de entrega:** completar, antes de presentar el PDF formal, las referencias bibliográficas completas y la verificación de condiciones de uso del dataset; no incluir capturas o fotografías ajenas sin atribución/autorización pertinente.
