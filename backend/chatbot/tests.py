from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from chatbot.models import ChatMessage, ChatAnalytics

User = get_user_model()


class ChatMessageModelTest(TestCase):
    """Test the ChatMessage model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test',
            first_name='User'
        )
    
    def test_create_chat_message(self):
        """Test creating a chat message"""
        message = ChatMessage.objects.create(
            user=self.user,
            message='Hello chatbot',
            response='Hello! How can I help you?'
        )
        self.assertEqual(message.user, self.user)
        self.assertEqual(message.message, 'Hello chatbot')
        self.assertEqual(message.response, 'Hello! How can I help you?')


class ChatAnalyticsModelTest(TestCase):
    """Test the ChatAnalytics model"""
    
    def test_create_chat_analytics(self):
        """Test creating chat analytics"""
        analytics = ChatAnalytics.objects.create(
            total_messages=100,
            successful_responses=95,
            failed_responses=5
        )
        self.assertEqual(analytics.total_messages, 100)
        self.assertEqual(analytics.successful_responses, 95)
        self.assertEqual(analytics.failed_responses, 5)


class ChatbotViewTest(TestCase):
    """Test chatbot views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test',
            first_name='User'
        )
    
    def test_chatbot_view(self):
        """Test chatbot view"""
        response = self.client.get(reverse('chatbot:chat'))
        self.assertEqual(response.status_code, 200)
    
    def test_authenticated_chatbot_view(self):
        """Test authenticated chatbot view"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('chatbot:chat'))
        self.assertEqual(response.status_code, 200)
