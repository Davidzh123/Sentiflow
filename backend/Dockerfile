<<<<<<< HEAD
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY pyproject.toml .

# Installer uv et les dépendances
RUN pip install uv && uv pip install --system -e .

# Installer les dépendances RAG/MLOps
RUN pip install pgvector sentence-transformers mlflow

# Copier le code
COPY backend/ backend/
COPY services/ services/
COPY features/ features/

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
=======
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY pyproject.toml .

# Installer uv et les dépendances
RUN pip install uv && uv pip install --system -e .

# Copier le code
COPY backend/ backend/
COPY services/ services/
COPY scripts/ scripts/

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> de7e700a57fde813194d5d256df032c07dda626c
