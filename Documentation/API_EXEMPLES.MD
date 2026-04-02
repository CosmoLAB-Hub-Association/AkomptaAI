# Exemples d'Utilisation de l'API Akompta

## 🔐 Authentification

### Inscription (Compte Personnel)

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+22890123456",
    "account_type": "personal",
    "agreed": true
  }'
```

**Réponse :**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "account_type": "personal",
    "is_premium": false
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### Inscription (Compte Business)

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "business@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone_number": "+22890987654",
    "account_type": "business",
    "business_name": "AgriTech Solutions",
    "sector": "Agriculture",
    "location": "Lomé, Togo",
    "ifu": "1234567890123",
    "agreed": true,
    "businessAgreed": true
  }'
```

### Connexion

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### Rafraîchir le Token

```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

### Récupérer le Profil

```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Modifier le Profil

```bash
curl -X PATCH http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+22890999888",
    "dark_mode": true
  }'
```

### Changer le Mot de Passe

```bash
curl -X POST http://localhost:8000/api/auth/change-password/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "SecurePass123!",
    "new_password": "NewSecurePass456!",
    "new_password2": "NewSecurePass456!"
  }'
```

## 📦 Produits

### Créer un Produit

```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tomates",
    "description": "Tomates fraîches de qualité",
    "price": "800.00",
    "unit": "Kg",
    "category": "vente",
    "stock_status": "ok"
  }'
```

### Créer un Produit avec Image

```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "name=Tomates" \
  -F "description=Tomates fraîches" \
  -F "price=800.00" \
  -F "unit=Kg" \
  -F "category=vente" \
  -F "stock_status=ok" \
  -F "image=@/path/to/image.jpg"
```

### Lister les Produits

```bash
# Tous les produits
curl -X GET http://localhost:8000/api/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Filtrer par catégorie
curl -X GET "http://localhost:8000/api/products/?category=vente" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Rechercher
curl -X GET "http://localhost:8000/api/products/?search=tomate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Pagination
curl -X GET "http://localhost:8000/api/products/?page=2" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Modifier un Produit

```bash
curl -X PUT http://localhost:8000/api/products/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tomates Premium",
    "price": "1000.00",
    "stock_status": "low"
  }'
```

### Supprimer un Produit

```bash
curl -X DELETE http://localhost:8000/api/products/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Exporter les Produits en CSV

```bash
curl -X GET http://localhost:8000/api/products/export/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o products.csv
```

## 💰 Transactions

### Créer une Transaction

```bash
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vente de tomates",
    "amount": "5000.00",
    "type": "income",
    "category": "Ventes",
    "date": "2024-11-27T10:30:00Z",
    "currency": "FCFA"
  }'
```

### Lister les Transactions

```bash
# Toutes les transactions
curl -X GET http://localhost:8000/api/transactions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Filtrer par type
curl -X GET "http://localhost:8000/api/transactions/?type=income" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Filtrer par période
curl -X GET "http://localhost:8000/api/transactions/?date_range=week" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Trier par date décroissante
curl -X GET "http://localhost:8000/api/transactions/?ordering=-date" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Rechercher
curl -X GET "http://localhost:8000/api/transactions/?search=vente" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Résumé des Transactions (Dashboard)

```bash
curl -X GET http://localhost:8000/api/transactions/summary/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Réponse :**
```json
{
  "balance": "125000.00",
  "income_24h": "15000.00",
  "expenses_24h": "8000.00",
  "income_variation": 12.5,
  "expenses_variation": -5.3
}
```

## 📊 Analytics

### Overview (Graphique en Barres)

```bash
curl -X GET http://localhost:8000/api/analytics/overview/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Réponse :**
```json
[
  {
    "month": "Oct 2024",
    "income": "85000.00",
    "expenses": "45000.00"
  },
  {
    "month": "Nov 2024",
    "income": "120000.00",
    "expenses": "65000.00"
  }
]
```

### Breakdown (Graphique Camembert)

```bash
curl -X GET http://localhost:8000/api/analytics/breakdown/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Réponse :**
```json
[
  {
    "category": "Transport",
    "amount": "25000.00",
    "percentage": 38.5
  },
  {
    "category": "Loyer",
    "amount": "40000.00",
    "percentage": 61.5
  }
]
```

### KPIs

```bash
curl -X GET http://localhost:8000/api/analytics/kpi/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Réponse :**
```json
{
  "average_basket": "12500.00",
  "estimated_mrr": "120000.00",
  "cac": "5000.00"
}
```

## 🎯 Budgets

### Créer un Budget

```bash
curl -X POST http://localhost:8000/api/budgets/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Transport",
    "limit": "50000.00",
    "color": "#3B82F6"
  }'
```

### Lister les Budgets

```bash
curl -X GET http://localhost:8000/api/budgets/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Réponse :**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "category": "Transport",
      "limit": "50000.00",
      "color": "#3B82F6",
      "spent_amount": "32500.00",
      "percentage": 65.0
    }
  ]
}
```

### Modifier un Budget

```bash
curl -X PUT http://localhost:8000/api/budgets/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": "75000.00"
  }'
```

### Supprimer un Budget

```bash
curl -X DELETE http://localhost:8000/api/budgets/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📢 Annonces

### Lister les Annonces (Public)

```bash
curl -X GET http://localhost:8000/api/ads/
```

### Créer une Annonce

```bash
curl -X POST http://localhost:8000/api/ads/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "product_name=Engrais Bio" \
  -F "owner_name=FertiTogo" \
  -F "description=Engrais biologique de qualité" \
  -F "whatsapp=+22890123456" \
  -F "location=Lomé, Togo" \
  -F "website=https://fertitogo.com" \
  -F "image=@/path/to/image.jpg"
```

### Rechercher des Annonces

```bash
curl -X GET "http://localhost:8000/api/ads/?search=engrais" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## ⚠️ Gestion des Erreurs

### Erreur de Validation

```json
{
  "type": "validation_error",
  "errors": {
    "email": ["Cet email existe déjà."],
    "ifu": ["Ce champ est obligatoire pour les comptes professionnels."]
  }
}
```

### Erreur d'Authentification

```json
{
  "type": "authentication_error",
  "message": "Token invalide ou expiré"
}
```

### Erreur de Permission

```json
{
  "type": "permission_error",
  "message": "Vous n'avez pas la permission d'effectuer cette action"
}
```

## 📝 Notes Importantes

1. **Toujours inclure le token** dans l'en-tête `Authorization: Bearer YOUR_TOKEN`
2. **Les dates** doivent être au format ISO 8601 : `2024-11-27T10:30:00Z`
3. **Les montants** sont en format décimal avec 2 décimales : `"1000.00"`
4. **Pagination** : Paramètres `?page=2&page_size=20`
5. **Upload de fichiers** : Utiliser `multipart/form-data` avec `-F`

## 🔄 Exemple Complet de Workflow

```bash
# 1. S'inscrire
TOKEN=$(curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","password2":"Test123!","first_name":"Test","last_name":"User","account_type":"personal","agreed":true}' \
  | jq -r '.tokens.access')

# 2. Créer un produit
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Tomates","price":"800.00","unit":"Kg","category":"vente","stock_status":"ok"}'

# 3. Ajouter une transaction
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Vente tomates","amount":"5000.00","type":"income","category":"Ventes","date":"2024-11-27T10:00:00Z"}'

# 4. Voir le résumé
curl -X GET http://localhost:8000/api/transactions/summary/ \
  -H "Authorization: Bearer $TOKEN"
```