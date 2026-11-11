# Plan de desarrollo — Image Forensics Lab
Actualizado noviembre de 2026. Se distinguen funciones implementadas de resultados científicamente validados.

## 1. Base técnica
- [x] Repositorio GitHub, backend FastAPI y frontend HTML/CSS/JS.
- [x] Validación de formato JPEG/PNG y límite de tamaño.
- [x] Dataset IMD2020 importado y auditado localmente (60 orígenes, 251 imágenes).
- [ ] Verificar condiciones/licencias y procedencia de datasets para el informe.

## 2. Procesamiento clásico
- [x] Histogramas RGB y escala de grises.
- [x] Canny, filtros gaussiano y mediana, residuo visual.
- [x] ELA JPEG calidad 90 con contraste visual configurable.
- [x] Comparación de dos imágenes alineadas, máscaras y F1/IoU de referencia.
- [ ] Umbralización y morfología explícitas; controles comparables y descarga.

## 3. ML experimental
- [x] Ocho características por parche 32×32.
- [x] Entrenamiento Random Forest y SVM con separación por origen.
- [x] Métricas y diagnósticos por fotografía.
- [x] Código de calibración F0.5 mediante validación; split bloqueado, baseline
      todo-normal y mapas TP/FP/FN (pendiente ejecutar sobre IMD2020 real).
- [ ] Ejecutar suite completa y calibración de 60 grupos en la computadora.
- [ ] Comparar trade-off precisión/recall y revisar mapas de fallas.
- [ ] Mejorar características solo si los experimentos justifican cambios.
- [ ] Evaluación final con datos nuevos **nunca inspeccionados** y métricas a nivel
      de parche y píxel; conservar un holdout fijo y documentar incertidumbre.

## 4. Aplicación y despliegue
- [x] Interfaces de análisis clásico y comparación en rama de desarrollo.
- [x] Inferencia ML local desde una sola imagen.
- [ ] Integrar inferencia ML en FastAPI y visualización web como herramienta
      EXPLORATORIA (sin afirmar detección confiable).
- [ ] Pruebas de integración, manejo de imágenes, rendimiento y errores.
- [ ] Verificar Vercel/Render, PR e integración a main.
- [ ] Exportación de resultados.

## 5. Entregable académico
- [ ] Informe: pregunta, metodología, esquema y licencias de datos, resultados,
      limitaciones, imágenes reales de TP/FP/FN, referencias y conclusiones.
- [ ] README reproducible completo y guion de defensa.
