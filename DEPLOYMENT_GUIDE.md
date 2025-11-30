# Guide de Déploiement - Akompta AI

## 🚀 Configuration de Production

### **Backend (Django)**

#### 1. Préparation du Backend

**Variables d'environnement à configurer :**

Créez un fichier `.env` sur votre serveur de production :

```bash
# Django Settings
SECRET_KEY=votre-secret-key-tres-securise-ici
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com,api.votre-domaine.com

# Database (PostgreSQL recommandé)
DATABASE_URL=postgresql://user:password@localhost:5432/akompta_db

# CORS - Autoriser votre frontend
CORS_ALLOWED_ORIGINS=https://votre-domaine.com,https://app.votre-domaine.com

# Gemini API
GEMINI_API_KEY=votre_cle_gemini_ici

# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
```

#### 2. Hébergement Backend

**Options recommandées :**

1. **Railway.app** (Gratuit jusqu'à 5$ de crédit) ✅
   - URL: https://railway.app
   - Déploiement automatique depuis GitHub
   - Base de données PostgreSQL incluse

2. **Render.com** (Plan gratuit disponible) ✅
   - URL: https://render.com
   - SSL automatique
   - PostgreSQL gratuit

3. **PythonAnywhere** (Plan gratuit limité)
   - URL: https://pythonanywhere.com

4. **DigitalOcean / AWS / Google Cloud** (Payant mais flexible)

**Commandes de déploiement :**

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Collecter les fichiers statiques
python manage.py collectstatic --noinput

# 3. Appliquer les migrations
python manage.py migrate

# 4. Créer un superuser
python manage.py createsuperuser

# 5. Lancer avec Gunicorn (production)
gunicorn Akompta.wsgi:application --bind 0.0.0.0:8000
```

---

### **Frontend (React + Vite)**

#### 1. Configuration de l'URL du Backend

Créez un fichier `.env.production` dans le dossier `frontend/` :

```bash
VITE_API_URL=https://api.votre-domaine.com/api
```

**Exemples d'URLs selon votre hébergement :**

- Railway: `VITE_API_URL=https://akompta-backend-production.up.railway.app/api`
- Render: `VITE_API_URL=https://akompta-backend.onrender.com/api`
- Vercel: `VITE_API_URL=https://api.akompta.com/api`

#### 2. Hébergement Frontend

**Options recommandées :**

1. **Vercel** (Gratuit, recommandé pour Vite/React) ✅✅✅
   - URL: https://vercel.com
   - Déploiement automatique
   - SSL gratuit
   - CDN mondial ultra-rapide

2. **Netlify** (Gratuit, excellent pour SPA) ✅✅
   - URL: https://netlify.com
   - CI/CD intégré
   - Formulaires gratuits

3. **GitHub Pages** (Gratuit mais configuration manuelle)

4. **Cloudflare Pages** (Gratuit, très rapide)

**Build pour la production :**

```bash
# 1. Installer les dépendances
npm install

# 2. Builder le projet
npm run build

# 3. Le dossier 'dist/' contient votre app prête
```

---

## 📋 **Checklist de Déploiement**

### Backend ✅

- [ ] `.env` configuré avec les bonnes variables
- [ ] `DEBUG=False` en production
- [ ] `ALLOWED_HOSTS` correctement configuré
- [ ] `CORS_ALLOWED_ORIGINS` inclut votre domaine frontend
- [ ] Base de données PostgreSQL configurée (pas SQLite)
- [ ] Migrations appliquées
- [ ] Fichiers statiques collectés
- [ ] Gunicorn installé et configuré
- [ ] SSL/HTTPS activé
- [ ] Clé API Gemini valide

### Frontend ✅

- [ ] `.env.production` créé avec `VITE_API_URL`
- [ ] Build de production testé localement
- [ ] CORS configuré côté backend pour accepter les requêtes
- [ ] SSL/HTTPS activé
- [ ] Tests de bout en bout effectués

---

## 🔧 **Exemple de Workflow Complet**

### **Scénario : Hébergement sur Railway (Backend) + Vercel (Frontend)**

#### **Étape 1 : Déployer le Backend sur Railway**

1. Créez un compte sur https://railway.app
2. Cliquez sur "New Project" → "Deploy from GitHub repo"
3. Sélectionnez votre repository
4. Railway détecte automatiquement Django
5. Ajoutez une base de données PostgreSQL
6. Configurez les variables d'environnement :
   ```
   SECRET_KEY=...
   DEBUG=False
   ALLOWED_HOSTS=*.up.railway.app,votre-domaine.com
   CORS_ALLOWED_ORIGINS=https://votre-app.vercel.app
   GEMINI_API_KEY=...
   ```
7. Railway génère une URL : `https://akompta-backend-production.up.railway.app`

#### **Étape 2 : Déployer le Frontend sur Vercel**

1. Créez un compte sur https://vercel.com
2. Cliquez sur "New Project" → Importez votre repository
3. Configurez le dossier root : `frontend/`
4. Ajoutez la variable d'environnement :
   ```
   VITE_API_URL=https://akompta-backend-production.up.railway.app/api
   ```
5. Cliquez sur "Deploy"
6. Vercel génère une URL : `https://akompta-ai.vercel.app`

#### **Étape 3 : Mettre à jour les CORS côté Backend**

Sur Railway, ajoutez l'URL Vercel dans `CORS_ALLOWED_ORIGINS` :
```
CORS_ALLOWED_ORIGINS=https://akompta-ai.vercel.app
```

#### **Étape 4 : Tester**

1. Visitez `https://akompta-ai.vercel.app`
2. Créez un compte
3. Testez les fonctionnalités (transactions, vocal, etc.)
4. Vérifiez que les données sont bien enregistrées

---

## 🔐 **Sécurité en Production**

### Backend

1. **Jamais de `DEBUG=True` en production**
2. **SECRET_KEY unique et complexe**
3. **HTTPS obligatoire** (SSL/TLS)
4. **CORS strictement configuré** (pas de wildcard `*`)
5. **Clés API dans variables d'environnement** (jamais dans le code)
6. **Limiter les requêtes** (rate limiting)
7. **Logs d'erreurs configurés**

### Frontend

1. **Pas de clés API sensibles** dans le code frontend
2. **Build de production optimisé** (minification)
3. **HTTPS obligatoire**
4. **Validation côté serveur** (jamais uniquement côté client)

---

## 🆘 **Dépannage**

### Problème : CORS Errors

**Erreur :** `Access to XMLHttpRequest blocked by CORS policy`

**Solution :**
```python
# backend/Akompta/settings.py
CORS_ALLOWED_ORIGINS = [
    'https://votre-frontend.vercel.app',
    'http://localhost:5173',  # Pour dev local
]
```

### Problème : 500 Internal Server Error

**Solution :**
1. Vérifiez les logs du serveur
2. Assurez-vous que `DEBUG=False` et `ALLOWED_HOSTS` est configuré
3. Vérifiez que toutes les migrations sont appliquées

### Problème : Static files non servis

**Solution :**
```bash
python manage.py collectstatic --noinput
```

Configurez dans `settings.py` :
```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

---

## 📞 **Support**

Pour toute question sur le déploiement :
1. Consultez cette documentation
2. Vérifiez les logs d'erreur
3. Testez localement d'abord

---

## 🎉 **Ressources Utiles**

- Django Deployment: https://docs.djangoproject.com/en/5.0/howto/deployment/
- Vite Production Build: https://vitejs.dev/guide/build.html
- Railway Docs: https://docs.railway.app/
- Vercel Docs: https://vercel.com/docs
