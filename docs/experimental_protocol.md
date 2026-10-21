# Protocolo experimental (borrador v0.1)

## Pregunta
¿Mejora un clasificador de regiones con características de procesamiento clásico la localización de manipulaciones respecto de métodos clásicos individuales?

## Unidad y separación
Fotografía original y parches derivados. Particionar train/validation/test por **fotografía original** antes de generar derivados; evitar fugas y documentar procedencia/cámara.

## Manipulaciones
- Copy-move: copiar y pegar un sector de la misma fotografía.
- Splicing: insertar una región proveniente de otra fotografía.
- Alteración controlada de color y textura.

Guardar fotografía original, fotografía manipulada, máscara binaria y metadatos (semilla, región, parámetros, operación). Validar la máscara contra los cambios efectivos.

## Métodos
- Referencias clásicas: gradientes, residuos de ruido y diferencia de recompresión JPEG; umbrales calibrados sobre validación.
- Random Forest sobre características por parche.
- SVM con iguales características y particiones.

## Evaluación
- Precisión, recall, F1 e IoU para máscaras con umbral fijado en validación.
- Medición por parche cuando corresponda, documentando la conversión de parches a mapa.
- Desglose por tipo, tamaño y compresión; análisis de falsos positivos y negativos.
- Registrar versiones, semillas, licencias y limitaciones.

## Límites
Los mapas JPEG o de ruido no constituyen prueba de falsificación; no extrapolar conclusiones a imágenes generadas por IA.
