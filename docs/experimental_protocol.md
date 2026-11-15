# Protocolo experimental — Image Forensics Lab

**Asignatura:** Procesamiento de Imágenes · IFTS N.º 18  
**Autora:** Fernanda Andrea Fava  
**Actualizado:** noviembre de 2026  
**Estado:** metodología implementada y evaluada de forma exploratoria; clasificador **EXPERIMENTAL_NO_VALIDADO**.

Este documento distingue el diseño original de las decisiones efectivamente utilizadas durante los ensayos. Para métricas detalladas, consultar el [informe técnico](informe_final.md); para el estado de implementación, consultar el [roadmap](roadmap.md).

## 1. Pregunta de investigación

¿Qué aportan las técnicas clásicas de procesamiento de imágenes a la visualización de cambios y en qué medida un clasificador supervisado por regiones puede localizar zonas modificadas **sin disponer de la imagen original**?

Se estudiaron dos escenarios diferentes:

1. **Comparación controlada con referencia:** comparar imágenes original y modificada, y contrastar una máscara de cambios con una máscara de referencia independiente.
2. **Clasificación experimental sin referencia:** extraer características de una única imagen y clasificar parches mediante aprendizaje supervisado.

Las métricas de uno y otro escenario **no son directamente intercambiables**.

## 2. Datos y unidad de análisis

Para los experimentos de aprendizaje automático se utilizó una muestra local de **IMD2020** con **251 imágenes**, organizadas en **60 grupos de fotografías de origen**. Se extrajeron **246.699 parches no solapados de 32 × 32 píxeles**.

- **Unidad de separación:** fotografía de origen (`group`), incluyendo todas sus versiones.
- **Unidad de clasificación:** parche de 32 × 32 píxeles.
- **Etiqueta positiva:** parche con al menos **10 %** de píxeles modificados según su máscara de referencia.
- **Partición por origen:** 36 grupos para entrenamiento, 12 para validación y 12 para prueba.
- **Trazabilidad:** se documentaron asignaciones de grupos y huella SHA256 del manifiesto en archivos locales.

Se separaron versiones derivadas del mismo origen para reducir fugas de información. Sin embargo, el conjunto de prueba fue inspeccionado durante el desarrollo; por eso **no constituye un benchmark final independiente**.

Las fotografías y máscaras externas no se distribuyen dentro del repositorio.

## 3. Manipulaciones y referencias

El diseño consideró operaciones como:

- **Copy-move:** copiar y pegar una región dentro de una misma fotografía.
- **Splicing:** insertar una región procedente de otra fotografía.
- **Cambios controlados:** alteraciones de color, textura o elementos visuales.

Estas operaciones describen tipos de alteración contemplados en el protocolo, **no una afirmación de que se haya generado y evaluado un dataset propio exhaustivo para cada tipo**.

Para la demostración de comparación se incluyen **tres escenas sintéticas guiadas** con versiones originales, modificadas y máscaras generadas en el navegador. Son ejemplos didácticos, distintos del conjunto IMD2020 de entrenamiento.

Una máscara de referencia debe representar el área efectivamente modificada y no derivarse de la predicción del modelo.

## 4. Técnicas clásicas y comparación con referencia

El laboratorio implementa:

- Bordes mediante **Canny** (umbrales 100/200).
- Histogramas de intensidad RGB y escala de grises.
- Suavizado gaussiano y de mediana, y residuo visual.
- **ELA** mediante recompresión JPEG de calidad 90 y visualización de diferencias.
- Comparación de dos imágenes del mismo tamaño con diferencia absoluta RGB y máscara de cambios (algún canal con diferencia mayor que 20).

Cuando se aporta una máscara independiente, el comparador calcula **precisión, recall, F1, IoU y TP/FP/FN/TN por píxel**. Estas medidas evalúan coincidencia respecto de una referencia, **no autenticidad**.

## 5. Clasificadores supervisados

Se exploraron modelos **Random Forest** y **SVM**, empleando características extraídas de parches.

Para el análisis comparativo SVM:

- **V1:** ocho características relacionadas con intensidad, dispersión, Laplaciano, bordes, gradiente, variabilidad RGB y residuo JPEG.
- **V2:** catorce características; agrega descriptores LBP y diferencias con respecto a parches vecinos.
- Se utilizó un **SVM con kernel RBF**, escalado de variables y ponderación de clases.
- La selección del umbral se realizó usando el conjunto de **validación**, con criterio **F0.5**, que prioriza precisión sobre recall.
- La comparación V1/V2 mantuvo la misma partición de grupos.

La predicción pública usa **SVM V1** y representa resultados por bloques de 32 × 32. La superficie señalada no equivale a una probabilidad ni a un porcentaje de imagen falsificada.

## 6. Evaluación y resultados

Se evaluaron métricas por parche y se revisaron falsos positivos y falsos negativos, incluyendo representaciones visuales de errores.

En la comparación V1/V2 documentada en el [informe técnico](informe_final.md):

| Métrica por parche | SVM V1 | SVM V2 |
|---|---:|---:|
| Precisión | 15,27 % | 13,22 % |
| Recall | 26,17 % | 29,78 % |
| F1 | 19,29 % | 18,31 % |
| Falsos positivos | 5.066 | 6.822 |

**Interpretación:** V2 aumentó la recuperación de parches positivos, pero también las falsas alarmas y no mejoró el F1 global. El rendimiento observado es insuficiente para afirmar detección confiable.

Las evaluaciones por parche no equivalen a segmentación precisa a nivel de píxel. Tampoco se debe interpretar un resultado de una imagen de demostración como medida de desempeño general.

## 7. Reproducibilidad y pruebas

El repositorio publica el código del procesamiento, los clasificadores y las pruebas automatizadas, junto con instrucciones en el [README](../README.md).

- Se documentó una ejecución local con **40 pruebas automáticas aprobadas**.
- Se realizaron pruebas manuales cargando imágenes en el frontend, utilizando el comparador y ejecutando inferencia del SVM V1 desde la interfaz pública.
- El modelo desplegado utiliza un artefacto numérico NPZ, cuya equivalencia numérica frente al SVM de origen fue comprobada.

Los datos externos, artefactos locales de entrenamiento y resultados intermedios no se distribuyen automáticamente; reproducir los experimentos requiere obtener los datos de sus fuentes y respetar sus condiciones de uso.

## 8. Limitaciones y alcance de las conclusiones

- ELA, bordes, ruido y residuos pueden reaccionar a **compresión, textura, cambios de iluminación o edición legítima**.
- El SVM produce falsos positivos y falsos negativos elevados.
- Las particiones por origen reducen fugas entre variantes, pero no reemplazan una **validación externa**.
- Los resultados experimentales no permiten concluir que el sistema detecte imágenes generadas por IA.
- No se certifica autenticidad, falsificación ni intención de manipulación.

**Conclusión:** el proyecto demuestra la implementación e integración de técnicas de procesamiento de imágenes, comparación controlada y clasificación experimental por parches. Su valor académico está en la metodología, la interpretación crítica de métricas y la documentación de límites, no en afirmar una capacidad forense validada.
