---
title: Akompta Backend
emoji: 💰
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
app_port: 7860
---

# Akompta AI - Backend API

Ceci est le backend de l'application **Akompta AI**, une plateforme de gestion financière et comptable. 

## 🚀 Déploiement sur Hugging Face Spaces

Ce backend est configuré pour s'exécuter dans un conteneur Docker.

### Configuration requise (Variables d'environnement)

Assurez-vous de configurer les variables suivantes dans les "Settings" de votre Space :

- `DEBUG`: `False`
- `SECRET_KEY`: Votre clé secrète Django
- `ALLOWED_HOSTS`: `*`
- `CORS_ALLOWED_ORIGINS`: `https://akompta-ai-flame.vercel.app`
- `GEMINI_API_KEY`: Votre clé API Google Gemini

## 🛠️ Technologies utilisées

- **Framework**: Django 5.2 + Django REST Framework
- **Authentification**: JWT (Simple JWT)
- **Base de données**: SQLite
- **Serveur de production**: Gunicorn
- **Statique**: WhiteNoise

---
Développé par **Marino ATOHOUN** pour **CosmoLAB Hub**.
