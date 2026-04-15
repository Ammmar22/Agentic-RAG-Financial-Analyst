# 1. Image de base légère avec Python 3.12
FROM python:3.12-slim

# 2. Répertoire de travail dans le conteneur
WORKDIR /app

# 3. Copier les fichiers de dépendances en premier (optimise le cache)
COPY requirements.txt .

# 4. Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copier tout le reste du code (main.py, Rag_Avance.py, etc.)
COPY . .

# 6. Exposer le port que FastAPI utilise
EXPOSE 8000

# 7. Commande pour lancer l'API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]