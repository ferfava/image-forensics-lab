# Migración de interfaz: FastAPI + web estática

Rama de trabajo: `feature/fastapi-web-migration`. La rama principal no se modifica.

## Arquitectura
- `frontend/`: HTML/CSS/JavaScript; despliegue previsto en Vercel.
- `backend/main.py`: FastAPI; despliegue previsto en Render.
- `src/image_forensics/`: algoritmos Python reutilizables, independientes de la interfaz.

## Ejecutar localmente
Instalar con `pip install -r backend/requirements.txt`.
Iniciar API desde la raíz: `uvicorn backend.main:app --reload`.
Servir frontend: `python -m http.server 5500 --directory frontend`.
Abrir `http://localhost:5500`.

## Desplegar
Render (servicio Python): instalación `pip install -r backend/requirements.txt`; inicio `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
Configurar `CORS_ORIGINS=https://TU-SITIO.vercel.app` en Render (dominio real).
Vercel: publicar `frontend` como sitio estático, sin comando de compilación.
En `frontend/config.js`, sustituir la URL local por la URL HTTPS real de Render antes de publicar.

## Estado y límites
La primera ruta de análisis genera un mapa Canny: es una visualización de bordes, **no** un detector de alteraciones. No se almacenan fotografías. La API mantiene el control de 12 MB y 16 megapíxeles de `decode_rgb`. Próximas fases: histogramas, ruido, ELA, máscaras, evaluación y modelos ML. Añadir pruebas de API y despliegue antes de fusionar a main.
