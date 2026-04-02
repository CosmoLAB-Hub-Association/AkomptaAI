from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Notification, SupportTicket

User = get_user_model()

class NotificationTests(APITestCase):
    """Tests pour les notifications"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.notifications_url = reverse('notification-list')
    
    def test_create_notification(self):
        """Test création de notification"""
        data = {
            'title': 'Test Notification',
            'message': 'This is a test message',
            'type': 'system'
        }
        response = self.client.post(self.notifications_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first().user, self.user)
    
    def test_list_notifications(self):
        """Test récupération de la liste des notifications"""
        Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test message',
            type='system'
        )
        response = self.client.get(self.notifications_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_mark_read(self):
        """Test marquer une notification comme lue"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test message',
            type='system'
        )
        url = reverse('notification-mark-read', args=[notification.id])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
    
    def test_mark_all_read(self):
        """Test marquer toutes les notifications comme lues"""
        Notification.objects.create(
            user=self.user,
            title='Test Notification 1',
            message='Message 1',
            type='system'
        )
        Notification.objects.create(
            user=self.user,
            title='Test Notification 2',
            message='Message 2',
            type='system'
        )
        url = reverse('notification-mark-all-read')
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.filter(is_read=True).count(), 2)


class SupportTicketTests(APITestCase):
    """Tests pour les tickets support"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.support_url = reverse('support-list')
    
    def test_create_ticket(self):
        """Test création de ticket"""
        data = {
            'subject': 'Help me',
            'message': 'I need help'
        }
        response = self.client.post(self.support_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SupportTicket.objects.count(), 1)
        self.assertEqual(SupportTicket.objects.first().user, self.user)
    
    def test_list_tickets(self):
        """Test récupération de la liste des tickets"""
        SupportTicket.objects.create(
            user=self.user,
            subject='Help me',
            message='I need help'
        )
        response = self.client.get(self.support_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
