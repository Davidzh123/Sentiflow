FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances
RUN pip install streamlit plotly altair httpx

# Copier le code frontend
COPY frontend/ frontend/

# Exposer le port Streamlit
EXPOSE 8501

# Commande de démarrage
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
