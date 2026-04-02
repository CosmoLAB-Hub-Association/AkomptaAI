from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone

from .models import Product, Transaction, Budget, Ad

User = get_user_model()


class AuthenticationTests(APITestCase):
    """Tests pour l'authentification"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
    
    def test_register_personal_account(self):
        """Test inscription compte personnel"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'account_type': 'personal',
            'agreed': True
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
    
    def test_register_business_without_ifu_fails(self):
        """Test que l'inscription business sans IFU échoue"""
        data = {
            'email': 'business@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'account_type': 'business',
            'business_name': 'Test Corp',
            'agreed': True,
            'businessAgreed': True
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ifu', response.data['errors'])
    
    def test_register_business_with_ifu_succeeds(self):
        """Test inscription business avec IFU réussit"""
        data = {
            'email': 'business@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'account_type': 'business',
            'business_name': 'Test Corp',
            'ifu': '123456789',
            'agreed': True,
            'businessAgreed': True
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_login_with_email(self):
        """Test connexion avec email"""
        # Créer un utilisateur
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        
        # Tenter la connexion
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)


class ProductTests(APITestCase):
    """Tests pour les produits"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.products_url = reverse('product-list')
    
    def test_create_product(self):
        """Test création de produit"""
        data = {
            'name': 'Tomates',
            'description': 'Tomates fraîches',
            'price': '500.00',
            'unit': 'Kg',
            'category': 'vente',
            'stock_status': 'ok'
        }
        response = self.client.post(self.products_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Product.objects.first().user, self.user)
    
    def test_list_products(self):
        """Test récupération de la liste des produits"""
        Product.objects.create(
            user=self.user,
            name='Tomates',
            price=Decimal('500.00'),
            category='vente'
        )
        response = self.client.get(self.products_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_products_by_category(self):
        """Test filtrage des produits par catégorie"""
        Product.objects.create(
            user=self.user,
            name='Tomates',
            price=Decimal('500.00'),
            category='vente'
        )
        Product.objects.create(
            user=self.user,
            name='Essence',
            price=Decimal('1000.00'),
            category='depense'
        )
        
        response = self.client.get(self.products_url + '?category=vente')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Tomates')


class TransactionTests(APITestCase):
    """Tests pour les transactions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.transactions_url = reverse('transaction-list')
    
    def test_create_transaction(self):
        """Test création de transaction"""
        data = {
            'name': 'Vente tomates',
            'amount': '5000.00',
            'type': 'income',
            'category': 'Ventes',
            'date': timezone.now().isoformat()
        }
        response = self.client.post(self.transactions_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
    
    def test_transaction_summary(self):
        """Test résumé des transactions"""
        now = timezone.now()
        
        # Créer des transactions
        Transaction.objects.create(
            user=self.user,
            name='Vente',
            amount=Decimal('10000.00'),
            type='income',
            category='Ventes',
            date=now
        )
        Transaction.objects.create(
            user=self.user,
            name='Achat',
            amount=Decimal('3000.00'),
            type='expense',
            category='Achats',
            date=now
        )
        
        summary_url = reverse('transaction-summary')
        response = self.client.get(summary_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['balance']), Decimal('7000.00'))


class BudgetTests(APITestCase):
    """Tests pour les budgets"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.budgets_url = reverse('budget-list')
    
    def test_create_budget(self):
        """Test création de budget"""
        data = {
            'category': 'Transport',
            'limit': '50000.00',
            'color': '#FF5733'
        }
        response = self.client.post(self.budgets_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Budget.objects.count(), 1)
    
    def test_budget_spent_amount_calculation(self):
        """Test calcul du montant dépensé"""
        # Créer un budget
        budget = Budget.objects.create(
            user=self.user,
            category='Transport',
            limit=Decimal('50000.00')
        )
        
        # Créer des dépenses dans cette catégorie
        Transaction.objects.create(
            user=self.user,
            name='Taxi',
            amount=Decimal('5000.00'),
            type='expense',
            category='Transport',
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            name='Essence',
            amount=Decimal('10000.00'),
            type='expense',
            category='Transport',
            date=timezone.now()
        )
        
        # Vérifier le calcul
        response = self.client.get(self.budgets_url)
        budget_data = response.data['results'][0]
        
        self.assertEqual(Decimal(budget_data['spent_amount']), Decimal('15000.00'))
        self.assertEqual(budget_data['percentage'], 30.0)


class AdTests(APITestCase):
    """Tests pour les annonces"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        self.client = APIClient()
        self.ads_url = reverse('ad-list')
    
    def test_list_ads_without_auth(self):
        """Test que les annonces sont accessibles sans authentification"""
        Ad.objects.create(
            user=self.user,
            product_name='Engrais bio',
            owner_name='AgriCorp',
            description='Engrais de qualité',
            whatsapp='+22890123456',
            location='Lomé',
            is_verified=True
        )
        
        response = self.client.get(self.ads_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_ad_requires_auth(self):
        """Test que la création d'annonce requiert l'authentification"""
        data = {
            'product_name': 'Test Product',
            'owner_name': 'Test Owner',
            'description': 'Test description',
            'whatsapp': '+22890123456',
            'location': 'Lomé'
        }
        response = self.client.post(self.ads_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ModelTests(TestCase):
    """Tests pour les modèles"""
    
    def test_user_creation_personal(self):
        """Test création utilisateur personnel"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            account_type='personal'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.account_type, 'personal')
        self.assertFalse(user.is_premium)
    
    def test_user_business_requires_ifu(self):
        """Test que les comptes business nécessitent un IFU"""
        from django.core.exceptions import ValidationError
        
        user = User(
            email='business@example.com',
            account_type='business',
            business_name='Test Corp',
            first_name='Jane',
            last_name='Smith'
        )
        user.set_password('TestPass123!')
        
        with self.assertRaises(ValidationError):
            user.save()
    
    def test_budget_spent_amount_method(self):
        """Test méthode get_spent_amount du Budget"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        
        budget = Budget.objects.create(
            user=user,
            category='Transport',
            limit=Decimal('50000.00')
        )
        
        Transaction.objects.create(
            user=user,
            name='Taxi',
            amount=Decimal('5000.00'),
            type='expense',
            category='Transport',
            date=timezone.now()
        )
        
        self.assertEqual(budget.get_spent_amount(), Decimal('5000.00'))