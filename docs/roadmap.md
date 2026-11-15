# Estado del proyecto — Image Forensics Lab

**Corte documental:** 15 de noviembre de 2026  
**Asignatura:** Procesamiento de Imágenes · IFTS N.º 18  
**Autora:** Fernanda Andrea Fava  
**Estado de entrega:** prototipo académico desarrollado, documentado y probado funcionalmente. El componente de aprendizaje automático sigue siendo **EXPERIMENTAL_NO_VALIDADO**.

> Este documento separa las funcionalidades implementadas y las pruebas realizadas de la validación científica. Que la aplicación funcione y genere resultados no significa que pueda certificar la autenticidad de una fotografía.

## 1. Funcionalidades implementadas

- [x] Frontend web en HTML, CSS y JavaScript, desplegado en Vercel.
- [x] Backend FastAPI en Python, desplegado en Render.
- [x] Navegación por las secciones del laboratorio.
- [x] Carga y análisis de imágenes JPEG/PNG.
- [x] Detección de bordes Canny; histogramas RGB y en escala de grises.
- [x] Filtros gaussiano y de mediana; visualización de residuos.
- [x] ELA con recompresión JPEG a calidad 90 y amplificación visual del contraste.
- [x] Comparador de imagen original y modificada, con máscara de diferencias.
- [x] Evaluación contra máscara de referencia independiente, cuando se proporciona: precisión, recall, F1, IoU y matriz TP/FP/FN/TN por píxel.
- [x] Tres escenas sintéticas guiadas, con pares original/editada y máscara de referencia generados en el navegador.
- [x] Inferencia experimental del SVM V1 por parches de 32 × 32, mediante la API pública, con superposición y máscara visual.

## 2. Experimentación y resultados

- [x] Importación y auditoría local de una muestra de IMD2020: **60 grupos de origen, 251 imágenes y 246.699 parches**.
- [x] Particiones agrupadas por fotografía de origen para reducir filtraciones entre versiones de una misma imagen.
- [x] Entrenamiento exploratorio de **Random Forest y SVM**.
- [x] Calibración de umbral del SVM utilizando validación y criterio F0.5.
- [x] Análisis de falsos positivos y falsos negativos, incluyendo mapas de error.
- [x] Comparación controlada de SVM V1 (8 características) y V2 (14 características) con la misma partición; V2 no mejoró el resultado global.
- [x] Exportación numérica del SVM V1 a `backend/assets/svm_v1.npz`, con comprobación de equivalencia numérica frente al modelo de origen.

**Resultado clave:** la cantidad de falsas alarmas y las limitaciones de la evaluación impiden presentar el SVM como un detector forense validado. Los resultados son **exploratorios**, no una estimación definitiva de rendimiento en imágenes nuevas.

## 3. Pruebas y verificación funcional

- [x] Se cargaron imágenes en el frontend y se probaron las técnicas clásicas de procesamiento, observando sus resultados.
- [x] Se realizaron pruebas de comparación entre imágenes y visualización de diferencias.
- [x] Se probó la inferencia del SVM V1 desde la interfaz pública, con máscara, superposición y superficie señalada.
- [x] Se comprobó previamente la integración entre frontend Vercel y backend Render.
- [x] **40 pruebas automáticas de Python aprobadas** en la ejecución local documentada tras integrar la exportación NPZ.

**Alcance de la verificación:** estas son pruebas realizadas durante el desarrollo. No se declara una nueva ejecución automatizada posterior a los últimos cambios visuales ni una comprobación de disponibilidad en tiempo real al 15/11/2026. La disponibilidad de servicios gratuitos puede variar.

## 4. Documentación y enlaces para la entrega

- [x] [README principal](../README.md): descripción, instalación, uso, arquitectura, resultados y limitaciones.
- [x] [Informe técnico y resultados](informe_final.md): documento académico en Markdown, accesible desde GitHub.
- [x] [Guion de demostración y defensa](guion_defensa.md).
- [x] [Protocolo experimental](experimental_protocol.md).
- [x] Código fuente, dependencias y pruebas versionadas en el repositorio.

**Repositorio:** https://github.com/ferfava/image-forensics-lab  
**Aplicación:** https://image-forensics-lab-frontend.vercel.app/  
**API de estado ML:** https://image-forensics-api-pi9r.onrender.com/api/ml/status

No se presupone que el docente exija un PDF o una presentación independiente: el informe y el guion están disponibles en el repositorio. El canal de entrega se adecuará a la habilitación del aula virtual; si no está habilitada, se compartirán los enlaces por Discord.

## 5. Limitaciones y posibles mejoras posteriores

- [ ] **Validación externa:** evaluar con fotografías nuevas e independientes que no se hayan inspeccionado durante el desarrollo.
- [ ] **Documentación de fuentes:** completar o verificar referencias bibliográficas y condiciones de uso de datos externos antes de redistribuirlos. El repositorio no incorpora el dataset IMD2020.
- [ ] **Mejoras opcionales:** ampliar experimentos de segmentación, métodos morfológicos o modelos profundos, siempre con evaluación independiente.
- [ ] **Mantenimiento opcional:** repetir pruebas de regresión y controles de disponibilidad tras futuros cambios en frontend, backend o despliegue.

Los puntos de esta sección son limitaciones, controles documentales o trabajo futuro; **no representan funcionalidades prometidas como ya implementadas**.

## Conclusión

**Image Forensics Lab** es un laboratorio académico funcional de procesamiento digital de imágenes, comparación controlada y clasificación por parches de carácter experimental. La entrega permite revisar el código, reproducir procedimientos y analizar resultados y errores. **No determina si una imagen es auténtica, falsa o generada por IA.**
