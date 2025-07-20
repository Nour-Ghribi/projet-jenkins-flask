# Utiliser une image Python officielle légère
FROM python:3.10-slim

# Définir le dossier de travail dans le container
WORKDIR /app

# Copier uniquement requirements.txt d'abord pour profiter du cache Docker
COPY app/requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le contenu du dossier app dans /app du container
COPY app/ .

# Exposer le port 5000 (Flask par défaut)
EXPOSE 5000

# Variables d'environnement Flask (pour que flask run écoute sur toutes les interfaces)
ENV FLASK_APP=app.py

ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development

# Commande pour lancer l'application Flask avec la CLI flask (plus propre)
CMD ["flask", "run"]
