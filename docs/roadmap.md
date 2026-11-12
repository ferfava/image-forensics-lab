# Estado de cierre — Image Forensics Lab
Actualizado: noviembre de 2026. Diferenciar implementación pública y validación científica.

## Implementado y medido
- [x] Frontend HTML/CSS/JS y backend FastAPI con conexión pública observada en navegador.
- [x] Menú 01–08 y navegación hacia secciones del laboratorio.
- [x] Tres casos de ejemplo guiados, con PNG original, editado y máscara generados localmente en el navegador.
- [x] Canny, histogramas RGB/grises, filtros gaussiano y mediana, residuo.
- [x] ELA JPEG calidad 90 con amplificación de contraste.
- [x] Comparación controlada de dos fotografías, máscara, métricas de referencia (precisión, recall, F1 e IoU) por píxel.
- [x] Dataset IMD2020 local: 60 grupos, 251 imágenes y 246.699 parches.
- [x] Random Forest y SVM exploratorios, calibración F0.5 y mapas TP/FP/FN.
- [x] Comparación V1 (8 variables) / V2 (14 variables) con split por grupo idéntico; V2 no mejoró globalmente.
- [x] 40 pruebas automáticas aprobadas en ejecución local después de incorporar la exportación numérica NPZ.
- [x] Merge a main de funcionalidades clásicas y ML local.
- [x] Interfaz ML experimental y endpoints opcionales con mensajes de disponibilidad y advertencias.
- [x] SVM V1 original probado localmente; exportado a `backend/assets/svm_v1.npz` con equivalencia numérica comprobada.
- [x] Ejecutadas 40 pruebas automáticas tras integrar el modelo portable.
- [x] ML experimental publicado en Render y comprobado desde Vercel (superposición, máscara y superficie señalada), manteniendo estado no validado.
- [x] Informe técnico académico: [informe_final.md](informe_final.md).
- [x] Guion de demostración y defensa: [guion_defensa.md](guion_defensa.md).

## Comprobaciones de cierre antes de compartir con el profesor
- [ ] Completar prueba manual final de las tres acciones de cada tarjeta (ML del ejemplo de escritorio verificado).
- [ ] Probar el sitio desde una sesión nueva sin caché, confirmando menú 01–08.
- [ ] Probar una comparación desde cero, con original y edición de iguales dimensiones y máscara opcional.
- [x] Confirmado despliegue público de Render con el SVM V1 y predicción visual en Vercel.
- [ ] Repetir revisión final de regresiones de UI; las 40 pruebas de Python estaban aprobadas antes de los últimos ajustes visuales.
- [ ] Completar referencias académicas y verificar los términos de uso del dataset e imágenes de demostración.
- [ ] Exportar el informe al formato de entrega solicitado por el profesor, adjuntar capturas originales y guardar respaldo.

## Fuera de alcance de esta entrega
- [ ] Validación externa de detector ML con fotografías nuevas y no inspeccionadas.
- [x] Demostrador ML público etiquetado explícitamente como no validado; **no** ofrecerlo ni describirlo como detector forense confiable.
- [ ] Otros experimentos, morfología avanzada o CNN, solo como trabajo futuro.

**Cierre académico propuesto:** laboratorio de procesamiento de imágenes funcional y proyecto de clasificación exploratoria. No certifica autenticidad.
