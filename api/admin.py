from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Product, Transaction, Budget, Ad, AIInsight


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    """Administration des insights IA"""
    list_display = ['user', 'created_at', 'context_hash']
    list_filter = ['created_at', 'user']
    search_fields = ['user__email', 'content']
    readonly_fields = ['created_at', 'context_hash']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administration des utilisateurs"""
    
    list_display = [
        'email', 'first_name', 'last_name', 'account_type',
        'is_premium', 'is_staff', 'date_joined'
    ]
    list_filter = ['account_type', 'is_premium', 'is_staff', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'business_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Informations de connexion', {
            'fields': ('email', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'phone_number', 'avatar')
        }),
        ('Type de compte', {
            'fields': ('account_type', 'is_premium')
        }),
        ('Informations Business', {
            'fields': ('business_name', 'sector', 'location', 'ifu', 'business_logo'),
            'classes': ('collapse',)
        }),
        ('Paramètres', {
            'fields': ('currency', 'language', 'dark_mode')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined', 'business_agreed_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'account_type'),
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Administration des produits"""
    
    list_display = [
        'name', 'user', 'price', 'unit', 'category',
        'stock_status', 'image_preview', 'created_at'
    ]
    list_filter = ['category', 'stock_status', 'created_at']
    search_fields = ['name', 'description', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'name', 'description')
        }),
        ('Tarification', {
            'fields': ('price', 'unit')
        }),
        ('Catégorisation', {
            'fields': ('category', 'stock_status')
        }),
        ('Image', {
            'fields': ('image', 'image_preview')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "Pas d'image"
    image_preview.short_description = "Aperçu"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Administration des transactions"""
    
    list_display = [
        'name', 'user', 'amount', 'currency', 'type',
        'category', 'date', 'created_at'
    ]
    list_filter = ['type', 'category', 'date', 'created_at']
    search_fields = ['name', 'user__email', 'category']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Transaction', {
            'fields': ('name', 'amount', 'currency', 'type', 'category', 'date')
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Administration des budgets"""
    
    list_display = [
        'category', 'user', 'limit', 'spent_display',
        'percentage_display', 'color_preview', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['category', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'spent_display', 'percentage_display']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Budget', {
            'fields': ('category', 'limit', 'color')
        }),
        ('Statistiques', {
            'fields': ('spent_display', 'percentage_display'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def spent_display(self, obj):
        return f"{obj.get_spent_amount()} FCFA"
    spent_display.short_description = "Montant dépensé"
    
    def percentage_display(self, obj):
        spent = obj.get_spent_amount()
        if obj.limit > 0:
            percentage = (spent / obj.limit) * 100
            color = 'green' if percentage < 80 else 'orange' if percentage < 100 else 'red'
            return format_html(
                '<span style="color: {};">{}</span>',
                color, f'{percentage:.1f}%'
            )
        return "0%"
    percentage_display.short_description = "Pourcentage"
    
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 30px; height: 30px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_preview.short_description = "Couleur"


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    """Administration des annonces"""
    
    list_display = [
        'product_name', 'owner_name', 'location',
        'is_verified', 'image_preview', 'created_at'
    ]
    list_filter = ['is_verified', 'created_at']
    search_fields = ['product_name', 'owner_name', 'description', 'location']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'product_name', 'owner_name', 'description')
        }),
        ('Localisation & Contact', {
            'fields': ('location', 'whatsapp', 'website')
        }),
        ('Image', {
            'fields': ('image', 'image_preview')
        }),
        ('Modération', {
            'fields': ('is_verified',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_ads', 'unverify_ads']
    
    def verify_ads(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f"{count} annonce(s) vérifiée(s).")
    verify_ads.short_description = "Vérifier les annonces sélectionnées"
    
    def unverify_ads(self, request, queryset):
        count = queryset.update(is_verified=False)
        self.message_user(request, f"{count} annonce(s) dé-vérifiée(s).")
    unverify_ads.short_description = "Retirer la vérification"
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "Pas d'image"
    image_preview.short_description = "Aperçu"


# Personnalisation du site admin
admin.site.site_header = "Akompta AI Administration"
admin.site.site_title = "Akompta Admin"
admin.site.index_title = "Bienvenue sur l'administration Akompta"