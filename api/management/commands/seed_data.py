"""
Commande Django pour créer des données de test
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import random

from api.models import Product, Transaction, Budget, Ad

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée des données de test pour Akompta AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer toutes les données existantes avant de créer de nouvelles données',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Suppression des données existantes...'))
            Product.objects.all().delete()
            Transaction.objects.all().delete()
            Budget.objects.all().delete()
            Ad.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('✓ Données supprimées'))

        # Créer des utilisateurs de test
        self.stdout.write('Création des utilisateurs...')
        
        # Utilisateur personnel
        personal_user, created = User.objects.get_or_create(
            email='demo@akompta.com',
            defaults={
                'first_name': 'Demo',
                'last_name': 'User',
                'account_type': 'personal',
                'phone_number': '+22890123456',
            }
        )
        if created:
            personal_user.set_password('demo123')
            personal_user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Utilisateur personnel créé: {personal_user.email}'))

        # Utilisateur business
        business_user, created = User.objects.get_or_create(
            email='business@akompta.com',
            defaults={
                'first_name': 'Business',
                'last_name': 'Owner',
                'account_type': 'business',
                'business_name': 'AgriTech Solutions',
                'sector': 'Agriculture',
                'location': 'Lomé, Togo',
                'ifu': '1234567890123',
                'phone_number': '+22890987654',
            }
        )
        if created:
            business_user.set_password('business123')
            business_user.business_agreed = True
            business_user.business_agreed_at = timezone.now()
            business_user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Utilisateur business créé: {business_user.email}'))

        # Créer des produits
        self.stdout.write('Création des produits...')
        products_data = [
            {'name': 'Tomates', 'price': '800', 'unit': 'Kg', 'category': 'vente', 'stock_status': 'ok'},
            {'name': 'Oignons', 'price': '600', 'unit': 'Kg', 'category': 'vente', 'stock_status': 'low'},
            {'name': 'Riz', 'price': '450', 'unit': 'Kg', 'category': 'stock', 'stock_status': 'ok'},
            {'name': 'Huile', 'price': '2500', 'unit': 'Litre', 'category': 'stock', 'stock_status': 'rupture'},
            {'name': 'Maïs', 'price': '350', 'unit': 'Kg', 'category': 'vente', 'stock_status': 'ok'},
        ]
        
        for user in [personal_user, business_user]:
            for prod_data in products_data:
                Product.objects.get_or_create(
                    user=user,
                    name=prod_data['name'],
                    defaults={
                        'description': f'{prod_data["name"]} de qualité premium',
                        'price': Decimal(prod_data['price']),
                        'unit': prod_data['unit'],
                        'category': prod_data['category'],
                        'stock_status': prod_data['stock_status'],
                    }
                )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(products_data) * 2} produits créés'))

        # Créer des transactions
        self.stdout.write('Création des transactions...')
        
        categories_income = ['Ventes', 'Services', 'Consultation']
        categories_expense = ['Transport', 'Loyer', 'Achats', 'Marketing', 'Salaires']
        
        now = timezone.now()
        transaction_count = 0
        
        for user in [personal_user, business_user]:
            # Transactions des 30 derniers jours
            for i in range(50):
                days_ago = random.randint(0, 30)
                trans_date = now - timedelta(days=days_ago)
                
                trans_type = random.choice(['income', 'expense'])
                
                if trans_type == 'income':
                    category = random.choice(categories_income)
                    amount = Decimal(random.randint(5000, 50000))
                    name = f'Vente {category}'
                else:
                    category = random.choice(categories_expense)
                    amount = Decimal(random.randint(1000, 30000))
                    name = f'Dépense {category}'
                
                Transaction.objects.create(
                    user=user,
                    name=name,
                    amount=amount,
                    type=trans_type,
                    category=category,
                    date=trans_date,
                    currency='FCFA'
                )
                transaction_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ {transaction_count} transactions créées'))

        # Créer des budgets
        self.stdout.write('Création des budgets...')
        
        budgets_data = [
            {'category': 'Transport', 'limit': '50000', 'color': '#3B82F6'},
            {'category': 'Marketing', 'limit': '100000', 'color': '#EF4444'},
            {'category': 'Achats', 'limit': '200000', 'color': '#10B981'},
        ]
        
        budget_count = 0
        for user in [personal_user, business_user]:
            for budget_data in budgets_data:
                Budget.objects.get_or_create(
                    user=user,
                    category=budget_data['category'],
                    defaults={
                        'limit': Decimal(budget_data['limit']),
                        'color': budget_data['color'],
                    }
                )
                budget_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ {budget_count} budgets créés'))

        # Créer des annonces
        self.stdout.write('Création des annonces...')
        
        ads_data = [
            {
                'product_name': 'Engrais Bio Premium',
                'owner_name': 'FertiTogo',
                'description': 'Engrais biologique de haute qualité pour toutes cultures. Augmentez vos rendements naturellement.',
                'whatsapp': '+22890111222',
                'location': 'Lomé, Togo',
                'is_verified': True,
            },
            {
                'product_name': 'Système d\'irrigation automatique',
                'owner_name': 'AgroTech Solutions',
                'description': 'Solutions d\'irrigation modernes pour optimiser votre consommation d\'eau.',
                'whatsapp': '+22890333444',
                'location': 'Kara, Togo',
                'is_verified': True,
            },
            {
                'product_name': 'Semences certifiées',
                'owner_name': 'SeedCorp Afrique',
                'description': 'Semences de maïs, riz et soja certifiées et adaptées au climat ouest-africain.',
                'whatsapp': '+22890555666',
                'location': 'Sokodé, Togo',
                'is_verified': True,
            },
        ]
        
        for ad_data in ads_data:
            Ad.objects.get_or_create(
                user=business_user,
                product_name=ad_data['product_name'],
                defaults=ad_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(ads_data)} annonces créées'))

        # Résumé
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('DONNÉES DE TEST CRÉÉES AVEC SUCCÈS'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('\nComptes de test :'))
        self.stdout.write(f'  • Personnel: demo@akompta.com / demo123')
        self.stdout.write(f'  • Business: business@akompta.com / business123')
        self.stdout.write(self.style.SUCCESS('\nVous pouvez maintenant tester l\'API !'))
        