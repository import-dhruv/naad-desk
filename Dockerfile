# Naad Desk — single-image production build (FastAPI + built React frontend)
FROM python:3.12-slim AS backend
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY knowledge ./knowledge
COPY recon ./recon
COPY eval ./eval
COPY scripts ./scripts
COPY frontend/dist ./frontend/dist
WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
