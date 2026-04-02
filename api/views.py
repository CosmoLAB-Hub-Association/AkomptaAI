from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend
import csv
import hashlib
import json
from django.http import HttpResponse
from django.conf import settings

from .models import Product, Transaction, Budget, Ad, Notification, SupportTicket, AIInsight
from .serializers import (
    UserSerializer, RegisterSerializer, ChangePasswordSerializer,
    ProductSerializer, TransactionSerializer, TransactionSummarySerializer,
    BudgetSerializer, AdSerializer, OverviewAnalyticsSerializer,
    BreakdownAnalyticsSerializer, KPISerializer, ActivityAnalyticsSerializer,
    BalanceHistorySerializer, NotificationSerializer, SupportTicketSerializer
)
from .gemini_service import GeminiService
from .groq_service import GroqService
from .assemblyai_service import AssemblyAIService
import tempfile
import os

User = get_user_model()


# ========== AUTHENTIFICATION ==========

class RegisterView(APIView):
    """Inscription d'un nouvel utilisateur"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user, context={'request': request}).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'type': 'validation_error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Connexion via email et mot de passe"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'type': 'validation_error',
                'errors': {
                    'email': ['Email et mot de passe requis.']
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate avec email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'type': 'validation_error',
                'errors': {
                    'email': ['Email ou mot de passe incorrect.']
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.check_password(password):
            return Response({
                'type': 'validation_error',
                'errors': {
                    'password': ['Email ou mot de passe incorrect.']
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'type': 'validation_error',
                'errors': {
                    'email': ['Ce compte est désactivé.']
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class ProfileView(APIView):
    """Récupération et mise à jour du profil"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request):
        serializer = UserSerializer(
            request.user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response({
            'type': 'validation_error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Changement de mot de passe"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({
                    'type': 'validation_error',
                    'errors': {
                        'old_password': ['Mot de passe actuel incorrect.']
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Mot de passe modifié avec succès.'
            })
        
        return Response({
            'type': 'validation_error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# ========== PRODUITS ==========

class ProductViewSet(viewsets.ModelViewSet):
    """CRUD pour les produits"""
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'stock_status']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export CSV des produits"""
        products = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Nom', 'Description', 'Prix', 'Unité', 'Catégorie', 'Stock'])
        
        for product in products:
            writer.writerow([
                product.name,
                product.description,
                product.price,
                product.unit,
                product.get_category_display(),
                product.get_stock_status_display()
            ])
        
        return response


# ========== TRANSACTIONS ==========

class TransactionViewSet(viewsets.ModelViewSet):
    """CRUD pour les transactions"""
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'category']
    search_fields = ['name', 'category']
    ordering_fields = ['date', 'amount']
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)
        
        # Filtre par date range
        date_range = self.request.query_params.get('date_range')
        if date_range:
            now = timezone.now()
            if date_range == 'today':
                start_date = now.replace(hour=0, minute=0, second=0)
            elif date_range == 'week':
                start_date = now - timedelta(days=7)
            elif date_range == 'month':
                start_date = now - timedelta(days=30)
            elif date_range == 'year':
                start_date = now - timedelta(days=365)
            else:
                start_date = None
            
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Résumé pour le dashboard"""
        user = request.user
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        day_before = now - timedelta(days=2)
        
        # Transactions des dernières 24h
        recent = Transaction.objects.filter(
            user=user,
            date__gte=yesterday
        )
        
        # Transactions des 24h précédentes
        previous = Transaction.objects.filter(
            user=user,
            date__gte=day_before,
            date__lt=yesterday
        )
        
        # Calculs
        income_24h = recent.filter(type='income').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        expenses_24h = recent.filter(type='expense').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        prev_income = previous.filter(type='income').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        prev_expenses = previous.filter(type='expense').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Balance totale
        total_income = Transaction.objects.filter(
            user=user, type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_expenses = Transaction.objects.filter(
            user=user, type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        balance = user.initial_balance + total_income - total_expenses
        
        # Variations en %
        def calc_variation(current, previous):
            if previous > 0:
                return float(((current - previous) / previous) * 100)
            return 0.0
        
        data = {
            'balance': balance,
            'income_24h': income_24h,
            'expenses_24h': expenses_24h,
            'income_variation': calc_variation(income_24h, prev_income),
            'expenses_variation': calc_variation(expenses_24h, prev_expenses)
        }
        
        serializer = TransactionSummarySerializer(data)
        return Response(serializer.data)


# ========== ANALYTICS ==========

class AnalyticsView(APIView):
    """Analytics pour le dashboard"""
    permission_classes = [IsAuthenticated]
    
    def get_overview(self, request):
        """Graphique barres: Revenus vs Dépenses par mois"""
        user = request.user
        now = timezone.now()
        six_months_ago = now - timedelta(days=180)
        
        transactions = Transaction.objects.filter(
            user=user,
            date__gte=six_months_ago
        )
        
        # Grouper par mois
        monthly_data = {}
        for t in transactions:
            month_key = t.date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'income': Decimal('0.00'), 'expenses': Decimal('0.00')}
            
            if t.type == 'income':
                monthly_data[month_key]['income'] += t.amount
            else:
                monthly_data[month_key]['expenses'] += t.amount
        
        # Formater pour le serializer
        result = []
        for month, data in sorted(monthly_data.items()):
            result.append({
                'month': datetime.strptime(month, '%Y-%m').strftime('%b %Y'),
                'income': data['income'],
                'expenses': data['expenses']
            })
        
        serializer = OverviewAnalyticsSerializer(result, many=True)
        return Response(serializer.data)
    
    def get_breakdown(self, request):
        """Graphique camembert: Dépenses par catégorie"""
        user = request.user
        
        expenses = Transaction.objects.filter(
            user=user,
            type='expense'
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        total_expenses = sum(item['total'] for item in expenses)
        
        result = []
        for item in expenses:
            percentage = float((item['total'] / total_expenses) * 100) if total_expenses > 0 else 0
            result.append({
                'category': item['category'],
                'amount': item['total'],
                'percentage': percentage
            })
        
        serializer = BreakdownAnalyticsSerializer(result, many=True)
        return Response(serializer.data)
    
    def get_kpi(self, request):
        """KPIs clés avec calcul de croissance"""
        user = request.user
        now = timezone.now()
        month_ago = now - timedelta(days=30)
        two_months_ago = now - timedelta(days=60)
        
        # --- Période Actuelle (30 derniers jours) ---
        current_income_tx = Transaction.objects.filter(
            user=user, type='income', date__gte=month_ago
        )
        current_total_income = current_income_tx.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        current_count_income = current_income_tx.count()
        current_avg_basket = current_total_income / current_count_income if current_count_income > 0 else Decimal('0.00')
        
        current_marketing = Transaction.objects.filter(
            user=user, type='expense', category__icontains='marketing', date__gte=month_ago
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # --- Période Précédente (30 à 60 jours) ---
        prev_income_tx = Transaction.objects.filter(
            user=user, type='income', date__gte=two_months_ago, date__lt=month_ago
        )
        prev_total_income = prev_income_tx.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        prev_count_income = prev_income_tx.count()
        prev_avg_basket = prev_total_income / prev_count_income if prev_count_income > 0 else Decimal('0.00')
        
        prev_marketing = Transaction.objects.filter(
            user=user, type='expense', category__icontains='marketing', date__gte=two_months_ago, date__lt=month_ago
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # --- Calcul des Croissances ---
        def calc_growth(current, prev):
            if prev == 0: return 100.0 if current > 0 else 0.0
            return float(((current - prev) / prev) * 100)

        data = {
            'average_basket': current_avg_basket,
            'average_basket_growth': calc_growth(current_avg_basket, prev_avg_basket),
            'estimated_mrr': current_total_income,
            'estimated_mrr_growth': calc_growth(current_total_income, prev_total_income),
            'cac': current_marketing,
            'cac_growth': calc_growth(current_marketing, prev_marketing)
        }
        
        serializer = KPISerializer(data)
        return Response(serializer.data)

    def get_activity(self, request):
        """Graphique d'activité: Ventes des 7 derniers jours"""
        user = request.user
        now = timezone.now().date()
        days = []
        
        # Récupérer les 7 derniers jours
        for i in range(6, -1, -1):
            day = now - timedelta(days=i)
            total_sales = Transaction.objects.filter(
                user=user,
                type='income',
                date=day
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            
            days.append({
                'day': day.strftime('%a'), # Lun, Mar, etc.
                'sales': total_sales
            })
            
        serializer = ActivityAnalyticsSerializer(days, many=True)
        return Response(serializer.data)

    def get_balance_history(self, request):
        """Historique du solde cumulé"""
        user = request.user
        # Récupérer toutes les transactions triées par date
        transactions = Transaction.objects.filter(user=user).order_by('date')
        
        history = []
        running_balance = user.initial_balance
        
        # Grouper par date pour éviter d'avoir trop de points si plusieurs transactions le même jour
        daily_balances = {}
        for t in transactions:
            if t.type == 'income':
                running_balance += t.amount
            else:
                running_balance -= t.amount
            
            daily_balances[t.date] = running_balance
            
        # Formater pour le frontend
        for date in sorted(daily_balances.keys()):
            history.append({
                'date': date.strftime('%d/%m'),
                'balance': daily_balances[date]
            })
            
        # Si pas de transactions, ajouter un point à zéro
        if not history:
            history.append({'date': timezone.now().strftime('%d/%m'), 'balance': Decimal('0.00')})
            
        serializer = BalanceHistorySerializer(history, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_overview(request):
    view = AnalyticsView()
    return view.get_overview(request)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_breakdown(request):
    view = AnalyticsView()
    return view.get_breakdown(request)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_kpi(request):
    view = AnalyticsView()
    return view.get_kpi(request)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_activity(request):
    view = AnalyticsView()
    return view.get_activity(request)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_balance_history(request):
    view = AnalyticsView()
    return view.get_balance_history(request)


# ========== BUDGETS ==========

class BudgetViewSet(viewsets.ModelViewSet):
    """CRUD pour les budgets"""
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)


# ========== ANNONCES ==========

class AdViewSet(viewsets.ModelViewSet):
    """CRUD pour les annonces"""
    serializer_class = AdSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['product_name', 'owner_name', 'description', 'location']
    
    def get_queryset(self):
        # Les annonces sont publiques mais filtrées par vérification
        return Ad.objects.filter(is_verified=True)
    
    def get_permissions(self):
        # Lecture publique, écriture authentifiée
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


# ========== NOTIFICATIONS ==========

class NotificationViewSet(viewsets.ModelViewSet):
    """CRUD pour les notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['patch'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all marked as read'})
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ========== SUPPORT ==========

class SupportTicketViewSet(viewsets.ModelViewSet):
    """CRUD pour les tickets support"""
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ========== VOICE AI ==========

class VoiceCommandView(APIView):
    """Traitement des commandes vocales via Gemini"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        audio_file = request.FILES.get('audio')
        text_command = request.data.get('text')
        
        if not audio_file and not text_command:
            return Response({'error': 'No audio file or text command provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            service = GeminiService()
            
            # Fetch user products for context
            user_products = Product.objects.filter(user=request.user)
            products_list = [
                {"name": p.name, "price": float(p.price), "unit": p.unit} 
                for p in user_products
            ]
            print(f"VoiceCommandView - Context Products: {products_list}")
            
            debug_url = None
            if audio_file:
                # --- DEBUG: Sauvegarder l'audio pour vérification ---
                try:
                    debug_dir = os.path.join(settings.MEDIA_ROOT, 'debug_voice')
                    os.makedirs(debug_dir, exist_ok=True)
                    
                    # Nettoyer le nom du fichier et ajouter un timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    debug_filename = f"voice_{timestamp}_{audio_file.name}"
                    debug_path = os.path.join(debug_dir, debug_filename)
                    
                    with open(debug_path, 'wb+') as destination:
                        for chunk in audio_file.chunks():
                            destination.write(chunk)
                    
                    debug_url = f"{request.build_absolute_uri(settings.MEDIA_URL)}debug_voice/{debug_filename}"
                    print(f"DEBUG AUDIO SAVED: {debug_path}")
                    
                    # Important: Réinitialiser le curseur après la sauvegarde pour Groq/Gemini
                    audio_file.seek(0)
                except Exception as e:
                    print(f"Error saving debug audio: {e}")
                # --- FIN DEBUG ---

                # Primary attempt: AssemblyAI (User's choice)
                print(f"Using AssemblyAI STT as primary")
                user_lang = getattr(request.user, 'language', 'fr').lower()
                audio_file.seek(0)
                assembly_service = AssemblyAIService()
                transcription = assembly_service.transcribe(audio_file, language=user_lang)
                used_provider = "AssemblyAI"
                
                if not transcription:
                    # Fallback 1: Groq
                    print(f"AssemblyAI STT failed, trying Groq as fallback with language: {user_lang}")
                    audio_file.seek(0)
                    groq_service = GroqService()
                    transcription = groq_service.transcribe(audio_file, language=user_lang)
                    used_provider = "Groq"
                
                if transcription:
                    print(f"Transcription successful ({used_provider}): {transcription}")
                    
                    # LLM Processing Fallback Chain
                    result = None
                    groq_service = GroqService() # reusing the service
                    
                    # Try Llama 3.3 70B
                    print("Attempting processing with llama-3.3-70b-versatile...")
                    result = groq_service.process_text_command(transcription, context_products=products_list, model="llama-3.3-70b-versatile")
                    
                    if not result:
                        # Try Llama 3.1 8B
                        print("Llama 3.3 70B failed, attempting with llama-3.1-8b-instant...")
                        result = groq_service.process_text_command(transcription, context_products=products_list, model="llama-3.1-8b-instant")
                    
                    if not result:
                        # Final resort: Gemini
                        print("All Groq LLMs failed, falling back to Gemini...")
                        gemini_service = GeminiService()
                        result = gemini_service.process_text_command(transcription, context_products=products_list)
                else:
                    # Fallback 2: Gemini's native voice processing
                    print("All STT services failed, falling back to Gemini native voice command")
                    audio_file.seek(0)
                    audio_bytes = audio_file.read()
                    mime_type = audio_file.content_type or 'audio/mp3'
                    gemini_service = GeminiService()
                    result = gemini_service.process_voice_command(audio_bytes, mime_type, context_products=products_list)
            else:
                # Direct text command processing with the same chain
                groq_service = GroqService()
                print("Processing text command with llama-3.3-70b-versatile...")
                result = groq_service.process_text_command(text_command, context_products=products_list, model="llama-3.3-70b-versatile")
                
                if not result:
                    print("Llama 3.3 70B failed, trying llama-3.1-8b-instant...")
                    result = groq_service.process_text_command(text_command, context_products=products_list, model="llama-3.1-8b-instant")
                
                if not result:
                    print("All Groq LLMs failed, falling back to Gemini...")
                    gemini_service = GeminiService()
                    result = gemini_service.process_text_command(text_command, context_products=products_list)
            
            print(f"VoiceCommandView - Result Intent: {result.get('intent')}")
            
            if result.get('intent') == 'create_transaction':
                data = result.get('data', {})
                print(f"VoiceCommandView - Transaction Data: {data}")
                
                # Ensure date is a full datetime string for TransactionSerializer
                raw_date = data.get('date')
                final_datetime = timezone.now() # Already aware if USE_TZ=True
                
                if raw_date:
                    try:
                        # If AI gives YYYY-MM-DD, combine with current time
                        parsed_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
                        # Make sure we create an aware datetime to avoid warnings
                        naive_dt = datetime.combine(parsed_date, timezone.now().time())
                        final_datetime = timezone.make_aware(naive_dt)
                    except:
                        pass
                
                # Prepare naming with fallback to transcription
                transcription_text = result.get('transcription', '')
                default_name = (transcription_text[:20] + '...') if len(transcription_text) > 20 else transcription_text
                
                transaction_data = {
                    'name': data.get('name') or default_name or 'Transaction Vocale',
                    'amount': data.get('amount'),
                    'type': data.get('type'),
                    'category': data.get('category', 'Divers'),
                    'currency': data.get('currency', 'FCFA'),
                    'date': final_datetime
                }
                
                # Use serializer to validate and save
                # We need to pass context={'request': request} so that create() method can access user
                serializer = TransactionSerializer(data=transaction_data, context={'request': request})
                
                if serializer.is_valid():
                    print("VoiceCommandView - Serializer is valid. Saving...")
                    serializer.save()
                    return Response({
                        'status': 'success',
                        'transcription': result.get('transcription'),
                        'transaction': serializer.data,
                        'debug_audio_url': debug_url
                    })
                else:
                     print(f"VoiceCommandView - Serializer Errors: {serializer.errors}")
                     return Response({
                        'status': 'error',
                        'transcription': result.get('transcription'),
                        'message': 'Validation failed',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)

            elif result.get('intent') == 'create_product':
                data = result.get('data', {})
                print(f"VoiceCommandView - Product Data: {data}")
                
                product_data = {
                    'name': data.get('name'),
                    'price': data.get('price'),
                    'unit': data.get('unit') or 'unité',
                    'description': data.get('description') or '',
                    'category': data.get('category') or 'stock',
                    'stock_status': data.get('stock_status') or 'ok'
                }
                
                # Map common AI terms to valid choices if needed
                if product_data['stock_status'] == 'instock': product_data['stock_status'] = 'ok'
                if product_data['stock_status'] == 'outofstock': product_data['stock_status'] = 'rupture'
                
                serializer = ProductSerializer(data=product_data, context={'request': request})
                if serializer.is_valid():
                    print("VoiceCommandView - Product Serializer is valid. Saving...")
                    serializer.save()
                    return Response({
                        'status': 'success',
                        'transcription': result.get('transcription'),
                        'product': serializer.data,
                        'debug_audio_url': debug_url
                    })
                else:
                    print(f"VoiceCommandView - Product Serializer Errors: {serializer.errors}")
                    return Response({
                        'status': 'error',
                        'transcription': result.get('transcription'),
                        'message': 'Product validation failed',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'status': 'processed',
                'transcription': result.get('transcription'),
                'intent': result.get('intent'),
                'data': result.get('data'),
                'error': result.get('error'),
                'debug_audio_url': debug_url
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIInsightsView(APIView):
    """Génération d'insights financiers via Gemini avec mise en mémoire en base de données"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        context_data = request.data.get('context', {})
        
        # Calculer un hash du contexte pour détecter les changements
        context_str = json.dumps(context_data, sort_keys=True)
        context_hash = hashlib.sha256(context_str.encode()).hexdigest()
        
        # Vérifier si un insight existe déjà pour ce contexte et cet utilisateur
        existing_insight = AIInsight.objects.filter(
            user=request.user, 
            context_hash=context_hash
        ).first()
        
        if existing_insight:
            return Response({'insights': existing_insight.content, 'cached': True})
        
        try:
            service = GeminiService()
            insights = service.process_insights(context_data)
            
            # Sauvegarder le nouvel insight
            AIInsight.objects.create(
                user=request.user,
                content=insights,
                context_hash=context_hash
            )
            
            return Response({'insights': insights, 'cached': False})
        except Exception as e:
            # En cas d'erreur de l'IA, essayer de renvoyer le dernier insight connu
            last_insight = AIInsight.objects.filter(user=request.user).first()
            if last_insight:
                return Response({'insights': last_insight.content, 'cached': True, 'error_fallback': str(e)})
                
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)