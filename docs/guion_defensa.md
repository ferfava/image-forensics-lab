# Guion de demostración y defensa — Image Forensics Lab

**Duración objetivo:** 5–7 minutos. **Preparación:** enlace público abierto, dos fotografías de las mismas dimensiones (referencia y edición controlada) y una máscara binaria opcional. No depender de ML durante la demo.

## Demostración en vivo

1. **Introducción (40 s):** «Image Forensics Lab permite observar características visuales con herramientas clásicas. Los resultados son exploratorios; no certifican autenticidad».
2. **Carga y análisis (1 min):** cargar una foto JPEG/PNG, ejecutar análisis, mostrar Canny y explicar que localiza cambios de intensidad.
3. **Histogramas y filtros (1 min):** recorrer RGB/grises, gaussiano, mediana y residuo; distinguir una representación visual de una conclusión forense.
4. **ELA (1 min):** mostrar original y mapa JPEG calidad 90, mover el control de contraste. Aclarar que el ajuste es visual, no cambia la medida ni prueba edición.
5. **Comparador (1–2 min):** cargar referencia y una versión con modificación conocida, conservando dimensiones. Mostrar diferencia, máscara y porcentaje. Si se dispone de máscara real independiente, cargarla y explicar precisión, recall, F1 e IoU **por píxel**.
6. **ML (1 min):** mostrar el informe y uno de los mapas de error locales. Contar que V1 (8 variables) y V2 (14) se evaluaron en las mismas particiones y V2 no mejoró globalmente. Evitar presentar la inferencia ML como funcionalidad pública.

## Respuestas breves

**¿Por qué usar OpenCV?** Permite aplicar procedimientos conocidos y reproducibles (Canny, filtros, histogramas), y extraer medidas cuantitativas.

**¿Qué diferencia hay entre ELA y un detector?** ELA revela diferencias de recompresión; no asigna una etiqueta validada de fraude.

**¿Por qué parches de 32×32?** Transforman cada fotografía en vectores de características locales para SVM/RF; sacrifican precisión espacial y contexto global.

**¿Cómo evitaste fuga entre versiones de una foto?** Separé por grupo de origen; todas las versiones del mismo original van juntas a train, validation o test.

**¿Por qué reentrenaste?** V1 generaba demasiadas falsas alarmas. Probé seis variables adicionales LBP/contexto para medir si ayudaban. V2 aumentó recall pero también falsos positivos: fue una hipótesis no confirmada.

**¿Qué significa una precisión del 15 %?** Que aproximadamente 15 de cada 100 parches marcados como positivos eran realmente positivos en el conjunto de prueba evaluado. No es accuracy global ni probabilidad de falsificación.

**¿El modelo está validado?** No. Los datos de prueba ya se inspeccionaron durante el proyecto; las métricas son exploratorias y se requiere un conjunto externo nuevo.

**¿Qué es F0.5?** Combina precisión y recall dando mayor importancia a precisión; el umbral se eligió en validación, nunca sobre las etiquetas de test dentro del script.

**¿Por qué no usar una CNN?** Sería una alternativa futura, pero el enfoque con características clásicas permite estudiar las señales y evaluar sus limitaciones de manera interpretable.

## Comprobación previa

- [ ] Abrir https://image-forensics-lab-frontend.vercel.app/ en una ventana privada.
- [ ] Verificar que se muestren las siete secciones del menú en orden.
- [ ] Cargar una imagen y comprobar Canny, histogramas, filtros y ELA.
- [ ] Comparar dos imágenes de iguales dimensiones; revisar máscara y métricas.
- [ ] Preparar capturas de respaldo por si Render tarda en responder.
- [ ] Corroborar referencias, autoría de imágenes y requisitos del profesor.

**Plan B:** usar capturas de resultados reales del laboratorio y los mapas de error guardados localmente; no inventar predicciones ni afirmar resultados de ensayos que no se ejecutaron.
