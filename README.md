---
title: Akompta Backend
emoji: 💰
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
app_port: 7860
---

# Akompta AI - Application de Gestion Financière
## Développé par Marino ATOHOUN pour CosmoLAB Hub

![Status](https://img.shields.io/badge/status-en%20développement-yellow)
![Backend](https://img.shields.io/badge/backend-Django%205.2-green)
![Frontend](https://img.shields.io/badge/frontend-React%2019-blue)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

---

## 📋 Description

Akompta AI est une application web moderne de gestion financière et comptable destinée aux petites et moyennes entreprises ainsi qu'aux particuliers en Afrique de l'Ouest. L'application offre une interface intuitive pour gérer les transactions, suivre les budgets, analyser les performances et bien plus encore.

### ✨ Fonctionnalités Principales

- 🔐 **Authentification sécurisée** - Comptes personnels et professionnels avec JWT
- 💰 **Gestion des transactions** - Suivi complet des revenus et dépenses
- 📦 **Gestion des produits** - Inventaire et catalogue produits
- 📊 **Analytics avancés** - Graphiques interactifs et KPIs en temps réel
- 💡 **Insights IA** - Analyse intelligente via Google Gemini
- 🎯 **Suivi budgétaire** - Définition et monitoring des budgets par catégorie
- 🔔 **Notifications** - Alertes et rappels personnalisés
- 🌙 **Mode sombre** - Interface adaptative jour/nuit
- 📱 **Responsive** - Optimisé pour mobile et desktop
- 🌍 **Multilingue** - Support Français (extensible)

---

## 🏗️ Architecture

### Backend
- **Framework**: Django 5.2 + Django REST Framework
- **Base de données**: SQLite (dev), PostgreSQL (prod recommandé)
- **Authentification**: JWT (djangorestframework-simplejwt)
- **API**: RESTful avec pagination, filtrage, recherche
- **Tests**: Django TestCase + pytest

### Frontend
- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite
- **HTTP Client**: Axios
- **Charts**: Recharts
- **IA**: Google Gemini API
- **Styling**: CSS Vanilla avec variables CSS
- **State Management**: React Context + Custom Hooks

---

## 🚀 Installation et Démarrage

### Prérequis

- Python 3.12+
- Node.js 18+
- npm ou yarn
- Git

### 1. Cloner le Projet

```bash
git clone [URL_DU_REPO]
cd akompta-ai
```

### 2. Configuration Backend

```bash
# Naviguer vers le dossier backend
cd backend

# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur (optionnel)
python manage.py createsuperuser

# Lancer le serveur de développement
python manage.py runserver
```

Le backend sera accessible sur **http://localhost:8000**

### 3. Configuration Frontend

```bash
# Ouvrir un nouveau terminal
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

Le frontend sera accessible sur **http://localhost:5173**

### 4. Variables d'Environnement

**Backend** - Créer `.env` à la racine du projet:
```env
SECRET_KEY=votre-clé-secrète-django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Email (optionnel pour reset password)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
```

**Frontend** - Créer `frontend/.env.local`:
```env
VITE_API_URL=http://localhost:8000/api
API_KEY=votre-clé-google-gemini
```

---

## 🧪 Tests

### Backend

```bash
cd backend
source venv/bin/activate

# Lancer tous les tests
python manage.py test

# Lancer des tests spécifiques
python manage.py test api.tests
python manage.py test api.tests_new

# Avec coverage
coverage run --source='.' manage.py test
coverage report
```

**Résultat actuel**: ✅ 22 tests passent avec succès

### Frontend

```bash
cd frontend

# Tests unitaires (à implémenter)
npm test

# Tests E2E (à implémenter)
npm run test:e2e
```

---

## 📚 Documentation

- **[INTEGRATION_LOG.md](./INTEGRATION_LOG.md)** - Journal détaillé de l'intégration
- **[API_REFERENCE.md](./API_REFERENCE.md)** - Documentation complète de l'API
- **Admin Django**: http://localhost:8000/admin
- **API Browsable**: http://localhost:8000/api

---

## 🗂️ Structure du Projet

```
akompta-ai/
├── backend/
│   ├── Akompta/              # Configuration Django
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── api/                  # Application principale
│   │   ├── models.py         # Modèles de données
│   │   ├── serializers.py    # Serializers DRF
│   │   ├── views.py          # ViewSets et vues
│   │   ├── urls.py           # Routes API
│   │   ├── admin.py          # Configuration admin
│   │   ├── tests.py          # Tests
│   │   └── migrations/       # Migrations DB
│   ├── manage.py
│   ├── requirements.txt
│   └── db.sqlite3
│
├── frontend/
│   ├── screens/              # Écrans de l'application
│   │   ├── AuthScreens.tsx
│   │   ├── DashboardScreen.tsx
│   │   ├── ManagementScreen.tsx
│   │   └── ...
│   ├── components/           # Composants réutilisables
│   │   ├── Shared.tsx
│   │   └── BottomNav.tsx
│   ├── context/              # Contexts React
│   │   └── AuthContext.tsx
│   ├── api.ts                # Client API Axios
│   ├── hooks.ts              # Custom hooks
│   ├── types.ts              # Types TypeScript
│   ├── constants.ts          # Constantes
│   ├── App.tsx               # Composant principal
│   ├── index.tsx             # Point d'entrée
│   ├── package.json
│   └── vite.config.ts
│
├── INTEGRATION_LOG.md        # Journal d'intégration
├── API_REFERENCE.md          # Référence API
└── README.md                 # Ce fichier
```

---

## 🔑 Endpoints API Principaux

### Authentification
- `POST /api/auth/register/` - Inscription
- `POST /api/auth/login/` - Connexion
- `GET /api/auth/me/` - Profil utilisateur
- `PATCH /api/auth/me/` - Mise à jour profil

### Transactions
- `GET /api/transactions/` - Liste des transactions
- `POST /api/transactions/` - Créer une transaction
- `GET /api/transactions/summary/` - Résumé financier

### Produits
- `GET /api/products/` - Liste des produits
- `POST /api/products/` - Créer un produit

### Budgets
- `GET /api/budgets/` - Liste des budgets
- `POST /api/budgets/` - Créer un budget

### Analytics
- `GET /api/analytics/overview/` - Vue d'ensemble
- `GET /api/analytics/breakdown/` - Répartition par catégorie
- `GET /api/analytics/kpi/` - Indicateurs clés

**Voir [API_REFERENCE.md](./API_REFERENCE.md) pour la documentation complète**

---

## 🎨 Captures d'Écran

*À ajouter*

---

## 🛣️ Roadmap

### Phase 1 - MVP ✅ (En cours)
- [x] Backend API complet
- [x] Authentification JWT
- [x] CRUD Transactions, Produits, Budgets
- [x] Analytics de base
- [x] Dashboard avec graphiques
- [ ] Intégration complète frontend-backend

### Phase 2 - Fonctionnalités Avancées
- [ ] Upload d'images (avatar, produits)
- [ ] Export PDF/Excel
- [ ] Notifications push
- [ ] Saisie vocale
- [ ] Mode hors-ligne
- [ ] Multi-devises

### Phase 3 - Optimisations
- [ ] Cache Redis
- [ ] Optimistic updates
- [ ] Lazy loading
- [ ] PWA
- [ ] Tests E2E complets

### Phase 4 - Déploiement
- [ ] Configuration production
- [ ] CI/CD
- [ ] Monitoring
- [ ] Documentation utilisateur
- [ ] Support multilingue complet

---

## 🤝 Contribution

Ce projet est développé par **Marino ATOHOUN** pour **CosmoLAB Hub**.

Pour contribuer:
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📝 Conventions de Code

### Backend (Python)
- PEP 8 pour le style
- Docstrings pour toutes les fonctions/classes
- Type hints quand possible
- Tests pour chaque nouvelle fonctionnalité

### Frontend (TypeScript)
- ESLint + Prettier
- Composants fonctionnels avec hooks
- Types TypeScript stricts
- Nommage descriptif

---

## 🐛 Problèmes Connus

- [ ] Upload d'images non implémenté
- [ ] Pagination frontend à améliorer
- [ ] Tests frontend à compléter
- [ ] Mode hors-ligne non disponible

Voir les [Issues](./issues) pour plus de détails.

---

## 📄 Licence

Propriétaire - CosmoLAB Hub  
Tous droits réservés © 2025

---

## 👥 Équipe

**Développeur Principal**: Marino ATOHOUN  
**Organisation**: CosmoLAB Hub  
**Contact**: support@cosmolabhub.com

---

## 🙏 Remerciements

- Django & Django REST Framework
- React & Vite
- Google Gemini AI
- Recharts
- Lucide Icons
- Toute la communauté open source

---

## 📞 Support

Pour toute question ou problème:
- **Email**: support@cosmolabhub.com
- **Documentation**: [INTEGRATION_LOG.md](./INTEGRATION_LOG.md)
- **API Reference**: [API_REFERENCE.md](./API_REFERENCE.md)

---

**Dernière mise à jour**: 2025-11-28  
**Version**: 0.1.0 (MVP en développement)

