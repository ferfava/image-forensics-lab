# Estado de cierre — Image Forensics Lab
Actualizado: 11 de noviembre de 2026. Diferenciar funcionalidades web y ML experimental.

## Implementado y medido
- [x] Frontend HTML/CSS/JS y backend FastAPI con conexión pública observada en navegador.
- [x] Menú unificado 01–07 y navegación hacia secciones del laboratorio.
- [x] Canny, histogramas RGB/grises, filtros gaussiano y mediana, residuo.
- [x] ELA JPEG calidad 90 con amplificación de contraste.
- [x] Comparación controlada de dos fotografías, máscara, métricas de referencia (precisión, recall, F1 e IoU) por píxel.
- [x] Dataset IMD2020 local: 60 grupos, 251 imágenes y 246.699 parches.
- [x] Random Forest y SVM exploratorios, calibración F0.5 y mapas TP/FP/FN.
- [x] Comparación V1 (8 variables) / V2 (14 variables) con split por grupo idéntico; V2 no mejoró globalmente.
- [x] 35 pruebas automáticas aprobadas en ejecución local informada antes de los cambios finales del menú.
- [x] Merge a main de funcionalidades clásicas y ML local.
- [x] Informe técnico académico: [informe_final.md](informe_final.md).
- [x] Guion de demostración y defensa: [guion_defensa.md](guion_defensa.md).

## Comprobaciones de cierre antes de compartir con el profesor
- [ ] Probar el sitio desde una sesión nueva sin caché, confirmando menú 01–07.
- [ ] Probar una comparación desde cero, con original y edición de iguales dimensiones y máscara opcional.
- [ ] Confirmar que el despliegue público de Render y Vercel responde de forma consistente.
- [ ] Volver a correr pytest localmente después de los últimos cambios (aunque solo afectaron HTML/CSS/JS/documentación).
- [ ] Completar referencias académicas y verificar los términos de uso del dataset e imágenes de demostración.
- [ ] Exportar el informe al formato de entrega solicitado por el profesor, adjuntar capturas originales y guardar respaldo.

## Fuera de alcance de esta entrega
- [ ] Validación externa de detector ML con fotografías nuevas y no inspeccionadas.
- [ ] Detector ML web público: no desplegar mientras el clasificador permanezca no validado.
- [ ] Otros experimentos, morfología avanzada o CNN, solo como trabajo futuro.

**Cierre académico propuesto:** laboratorio de procesamiento de imágenes funcional y proyecto de clasificación exploratoria. No certifica autenticidad.
