---
title: Akompta Backend
emoji: 💰
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# Akompta AI - Backend API

Ceci est le backend de l'application **Akompta AI**, une plateforme de gestion financière et comptable. 

## 🚀 Déploiement sur Hugging Face Spaces

Ce backend est configuré pour s'exécuter dans un conteneur Docker sur Hugging Face Spaces.

### Configuration requise (Variables d'environnement)

Pour que l'API fonctionne correctement, assurez-vous de configurer les variables suivantes dans les "Settings" de votre Space :

- `DEBUG`: `False`
- `SECRET_KEY`: Votre clé secrète Django
- `ALLOWED_HOSTS`: `*`
- `CORS_ALLOWED_ORIGINS`: `https://akompta-ai-flame.vercel.app` (ou l'URL de votre frontend)
- `GEMINI_API_KEY`: Votre clé API Google Gemini

## 🛠️ Technologies utilisées

- **Framework**: Django 5.2 + Django REST Framework
- **Authentification**: JWT (Simple JWT)
- **Base de données**: SQLite
- **Serveur de production**: Gunicorn
- **Statique**: WhiteNoise

## 📂 Structure du Backend

- `Akompta/`: Configuration du projet Django
- `api/`: Application principale contenant les modèles, vues et logic métier
- `static/`: Fichiers statiques collectés
- `Dockerfile`: Configuration pour le déploiement
- `start.sh`: Script de démarrage pour l'application

## 🔗 Liens Utiles

- **Documentation API**: [API_REFERENCE.md](../API_REFERENCE.md)
- **Frontend Vercel**: [https://akompta-ai-flame.vercel.app](https://akompta-ai-flame.vercel.app)
- **Organisation**: CosmoLAB Hub

---
Développé par **Marino ATOHOUN** pour **CosmoLAB Hub**.
