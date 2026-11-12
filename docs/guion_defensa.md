# Guion de demostración y defensa — Image Forensics Lab

**Duración objetivo:** 5–7 minutos. **Preparación:** enlace público abierto, un caso guiado del laboratorio y capturas de respaldo por si el servicio gratuito demora en responder. El SVM V1 está disponible públicamente, pero sigue sin validación científica.

## Demostración en vivo

1. **Introducción (40 s):** «Image Forensics Lab permite observar características visuales con herramientas clásicas. Los resultados son exploratorios; no certifican autenticidad».
2. **Carga y análisis (1 min):** cargar una foto JPEG/PNG, ejecutar análisis, mostrar Canny y explicar que localiza cambios de intensidad.
3. **Histogramas y filtros (1 min):** recorrer RGB/grises, gaussiano, mediana y residuo; distinguir una representación visual de una conclusión forense.
4. **ELA (1 min):** mostrar original y mapa JPEG calidad 90, mover el control de contraste. Aclarar que el ajuste es visual, no cambia la medida ni prueba edición.
5. **Comparador (1–2 min):** elegir **«Faro y señal → Probar comparación»**; el frontend carga original, versión editada y máscara de referencia independiente. Mostrar diferencia, porcentaje y métricas de precisión, recall, F1 e IoU **por píxel**.
6. **ML (1 min):** elegir **«Escritorio y nota → Probar SVM»** y mostrar la superposición roja y la máscara generadas por el SVM V1 público. Explicar que el porcentaje señalado **no** es porcentaje de falsificación; mencionar que V2 (14 variables) no mejoró globalmente a V1 (8 variables), y que la inferencia pública demuestra integración técnica, no detección fiable.

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
- [ ] Verificar que se muestren las ocho secciones del menú y los tres ejemplos guiados.
- [ ] Cargar una imagen y comprobar Canny, histogramas, filtros y ELA.
- [ ] Ejecutar un ejemplo guiado en el comparador; revisar máscara y métricas.
- [ ] Ejecutar «Probar SVM» y comprobar superposición, máscara y porcentaje en el frontend público.
- [ ] Preparar capturas de respaldo por si Render tarda en responder.
- [ ] Corroborar referencias, autoría de imágenes y requisitos del profesor.

**Plan B:** usar capturas de resultados reales del laboratorio y los mapas de error guardados localmente; no inventar predicciones ni afirmar resultados de ensayos que no se ejecutaron.
