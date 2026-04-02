from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import Product, Transaction, Budget, Ad, Notification, SupportTicket

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'avatar', 'account_type', 'is_premium', 'initial_balance',
            'business_name', 'sector', 'location', 'ifu', 'business_logo',
            'currency', 'language', 'dark_mode',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription"""
    
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    agreed = serializers.BooleanField(write_only=True, required=True)
    businessAgreed = serializers.BooleanField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password2', 'first_name', 'last_name',
            'phone_number', 'account_type', 'business_name', 'sector',
            'location', 'ifu', 'agreed', 'businessAgreed'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas."
            })
        
        # Validation IFU pour les comptes business
        if attrs.get('account_type') == 'business':
            if not attrs.get('ifu'):
                raise serializers.ValidationError({
                    "ifu": "Ce champ est obligatoire pour les comptes professionnels."
                })
            if not attrs.get('businessAgreed'):
                raise serializers.ValidationError({
                    "businessAgreed": "Vous devez accepter les conditions professionnelles."
                })
        
        if not attrs.get('agreed'):
            raise serializers.ValidationError({
                "agreed": "Vous devez accepter les conditions générales."
            })
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data.pop('agreed')
        business_agreed = validated_data.pop('businessAgreed', False)
        
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        
        user.agreed_terms = True
        if business_agreed:
            user.business_agreed = True
            user.business_agreed_at = timezone.now()
        user.save()
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, 
        validators=[validate_password]
    )
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password": "Les mots de passe ne correspondent pas."
            })
        return attrs


class ProductSerializer(serializers.ModelSerializer):
    """Serializer pour les produits"""
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'unit', 'image',
            'category', 'stock_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer pour les transactions"""
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'name', 'amount', 'type', 'category', 'date',
            'currency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TransactionSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé des transactions (dashboard)"""
    
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    income_24h = serializers.DecimalField(max_digits=15, decimal_places=2)
    expenses_24h = serializers.DecimalField(max_digits=15, decimal_places=2)
    income_variation = serializers.FloatField()
    expenses_variation = serializers.FloatField()


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer pour les budgets"""
    
    spent_amount = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = [
            'id', 'category', 'limit', 'color', 'spent_amount',
            'percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'spent_amount', 'percentage', 'created_at', 'updated_at']
    
    def get_spent_amount(self, obj):
        return obj.get_spent_amount()
    
    def get_percentage(self, obj):
        spent = obj.get_spent_amount()
        if obj.limit > 0:
            return float((spent / obj.limit) * 100)
        return 0.0
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AdSerializer(serializers.ModelSerializer):
    """Serializer pour les annonces"""
    
    class Meta:
        model = Ad
        fields = [
            'id', 'product_name', 'owner_name', 'description', 'image',
            'whatsapp', 'website', 'location', 'is_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OverviewAnalyticsSerializer(serializers.Serializer):
    """Serializer pour les analytics overview (graphique barres)"""
    
    month = serializers.CharField()
    income = serializers.DecimalField(max_digits=15, decimal_places=2)
    expenses = serializers.DecimalField(max_digits=15, decimal_places=2)


class BreakdownAnalyticsSerializer(serializers.Serializer):
    """Serializer pour le breakdown des dépenses (camembert)"""
    
    category = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    percentage = serializers.FloatField()


class KPISerializer(serializers.Serializer):
    """Serializer pour les KPIs"""
    
    average_basket = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_basket_growth = serializers.FloatField(default=0.0)
    estimated_mrr = serializers.DecimalField(max_digits=15, decimal_places=2)
    estimated_mrr_growth = serializers.FloatField(default=0.0)
    cac = serializers.DecimalField(max_digits=15, decimal_places=2)
    cac_growth = serializers.FloatField(default=0.0)


class ActivityAnalyticsSerializer(serializers.Serializer):
    """Serializer pour l'activité hebdomadaire"""
    day = serializers.CharField()
    sales = serializers.DecimalField(max_digits=15, decimal_places=2)


class BalanceHistorySerializer(serializers.Serializer):
    """Serializer pour l'historique du solde"""
    date = serializers.CharField()
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications"""
    
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'message', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']


class SupportTicketSerializer(serializers.ModelSerializer):
    """Serializer pour les tickets support"""
    
    class Meta:
        model = SupportTicket
        fields = ['id', 'subject', 'message', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)