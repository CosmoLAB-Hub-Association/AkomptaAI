from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from decimal import Decimal


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password"""
        if not email:
            raise ValueError('L\'adresse email est obligatoire')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Modèle utilisateur étendu pour Akompta"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('personal', 'Personnel'),
        ('business', 'Professionnel'),
    ]
    
    # Utiliser email comme identifiant
    username = None
    email = models.EmailField(unique=True, verbose_name="Email")
    
    # Champs communs
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    account_type = models.CharField(
        max_length=10, 
        choices=ACCOUNT_TYPE_CHOICES, 
        default='personal'
    )
    is_premium = models.BooleanField(default=False)
    initial_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Champs Business
    business_name = models.CharField(max_length=255, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
    ifu = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="Identifiant Fiscal Unique"
    )
    business_logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    
    # Settings (Stockés en JSON)
    currency = models.CharField(max_length=10, default='XOF')
    language = models.CharField(max_length=5, default='FR')
    dark_mode = models.BooleanField(default=False)
    
    # Acceptation des conditions
    agreed_terms = models.BooleanField(default=False)
    business_agreed = models.BooleanField(default=False)
    business_agreed_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Custom manager
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # Validation IFU pour les comptes business
        if self.account_type == 'business' and not self.ifu:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                "Le champ IFU est obligatoire pour les comptes professionnels."
            )
        super().save(*args, **kwargs)


class Product(models.Model):
    """Modèle pour les produits/inventaire"""
    
    CATEGORY_CHOICES = [
        ('vente', 'Vente'),
        ('depense', 'Dépense'),
        ('stock', 'Stock'),
    ]
    
    STOCK_STATUS_CHOICES = [
        ('ok', 'OK'),
        ('low', 'Faible'),
        ('rupture', 'Rupture'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    unit = models.CharField(max_length=50, default='Unité')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    stock_status = models.CharField(
        max_length=10, 
        choices=STOCK_STATUS_CHOICES, 
        default='ok'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"


class Transaction(models.Model):
    """Modèle pour les transactions financières"""
    
    TYPE_CHOICES = [
        ('income', 'Revenu'),
        ('expense', 'Dépense'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=100)
    date = models.DateTimeField()
    currency = models.CharField(max_length=10, default='FCFA')
    
    # Support pour la synchro hors-ligne
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.amount} {self.currency}"


class Budget(models.Model):
    """Modèle pour les budgets suivis"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.CharField(max_length=100)
    limit = models.DecimalField(max_digits=15, decimal_places=2)
    color = models.CharField(max_length=7, default='#4F46E5')  # Hex color
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        unique_together = ['user', 'category']
    
    def __str__(self):
        return f"{self.category} - {self.limit}"
    
    def get_spent_amount(self):
        """Calcule le montant dépensé pour cette catégorie"""
        from django.db.models import Sum
        result = self.user.transactions.filter(
            type='expense',
            category=self.category
        ).aggregate(total=Sum('amount'))
        return result['total'] or Decimal('0.00')


class Ad(models.Model):
    """Modèle pour les annonces partenaires"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ads')
    product_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='ads/')
    whatsapp = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Annonce"
        verbose_name_plural = "Annonces"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product_name} - {self.owner_name}"


class Notification(models.Model):
    """Modèle pour les notifications"""
    
    TYPE_CHOICES = [
        ('reminder', 'Rappel'),
        ('profit', 'Profit'),
        ('promo', 'Promo'),
        ('system', 'Système'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"


class SupportTicket(models.Model):
    """Modèle pour le support client"""
    
    STATUS_CHOICES = [
        ('open', 'Ouvert'),
        ('in_progress', 'En cours'),
        ('closed', 'Fermé'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ticket Support"
        verbose_name_plural = "Tickets Support"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.status}"


class AIInsight(models.Model):
    """Modèle pour stocker les insights générés par l'IA"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_insights')
    content = models.JSONField()  # Liste de phrases
    context_hash = models.CharField(max_length=64)  # Hash des données utilisées pour la génération
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Insight IA"
        verbose_name_plural = "Insights IA"
        ordering = ['-created_at']

    def __str__(self):
        return f"Insight pour {self.user.email} - {self.created_at}"


class SyscohadaCRMappingRule(models.Model):
    """
    Règle de mapping Transaction -> Compte de résultat SYSCOHADA (ref).

    Objectif: rendre le calcul traçable et configurable par utilisateur.
    Le moteur tente d'appliquer la règle la plus prioritaire qui match
    (type + catégorie/nom via contains ou regex).
    """

    MATCH_MODE_CHOICES = [
        ("contains", "Contient"),
        ("regex", "Regex"),
    ]

    TX_TYPE_CHOICES = [
        ("income", "Revenu"),
        ("expense", "Dépense"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="syscohada_cr_rules")

    # Référence SYSCOHADA (ex: TA, TC, RA, RG, RH, RJ, ...)
    ref = models.CharField(max_length=4)

    # Optionnel: limiter aux revenus/dépenses
    tx_type = models.CharField(max_length=10, choices=TX_TYPE_CHOICES, blank=True, null=True)

    # Champs sur lesquels matcher
    category_pattern = models.CharField(max_length=255, blank=True, default="")
    name_pattern = models.CharField(max_length=255, blank=True, default="")
    match_mode = models.CharField(max_length=20, choices=MATCH_MODE_CHOICES, default="contains")

    # Plus petit = plus prioritaire
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Règle SYSCOHADA (CR)"
        verbose_name_plural = "Règles SYSCOHADA (CR)"
        ordering = ["priority", "-updated_at", "-id"]
        indexes = [
            models.Index(fields=["user", "is_active", "priority"]),
            models.Index(fields=["user", "tx_type"]),
            models.Index(fields=["user", "ref"]),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.ref} (prio {self.priority})"


class SyscohadaBilanBalance(models.Model):
    """
    Soldes SYSCOHADA saisis/importés (bilan) par utilisateur et exercice.

    Important:
    - Akompta n'ayant pas (encore) une comptabilité en partie double,
      beaucoup de postes du bilan doivent être saisis (ou importés).
    - Le système auto-calcule BS (trésorerie) et CJ (résultat net) à partir
      des transactions + compte de résultat.
    """

    SECTION_CHOICES = [
        ("ACTIF", "Actif"),
        ("PASSIF", "Passif"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="syscohada_bilan_balances")
    year = models.PositiveIntegerField()
    section = models.CharField(max_length=10, choices=SECTION_CHOICES)

    # Référence SYSCOHADA (ex: BS, BI, CA, DJ, ...)
    ref = models.CharField(max_length=4)

    # Actif: BRUT/AMORT pour calculer NET. Passif: NET uniquement.
    brut = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    amort = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    net = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    note = models.CharField(max_length=50, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Solde SYSCOHADA (Bilan)"
        verbose_name_plural = "Soldes SYSCOHADA (Bilan)"
        ordering = ["year", "section", "ref"]
        unique_together = ["user", "year", "section", "ref"]
        indexes = [
            models.Index(fields=["user", "year", "section"]),
            models.Index(fields=["user", "year", "ref"]),
        ]

    def __str__(self):
        return f"{self.user.email} {self.year} {self.section} {self.ref}"
        
