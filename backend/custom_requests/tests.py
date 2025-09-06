from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from custom_requests.models import ServiceRequest, Message, Document, RendezVous, ContactMessage
from services.models import ServiceCategory, ServiceType, Service
from accounts.models import Expert
from decimal import Decimal
from datetime import date, datetime

User = get_user_model()


class ServiceRequestModelTest(TestCase):
    """Test the ServiceRequest model"""
    
    def setUp(self):
        self.client_user = User.objects.create_user(
            email='client@example.com',
            password='testpass123',
            name='Client',
            first_name='User',
            account_type='client'
        )
        self.expert_user = User.objects.create_user(
            email='expert@example.com',
            password='testpass123',
            name='Expert',
            first_name='User',
            account_type='expert'
        )
        self.category = ServiceCategory.objects.create(
            name='Tourism',
            slug='tourism'
        )
        self.service_type = ServiceType.objects.create(
            category=self.category,
            name='City Tours',
            price=Decimal('50.00')
        )
        self.service = Service.objects.create(
            service_type=self.service_type,
            title='Paris Tour',
            description='City tour',
            price=Decimal('75.00')
        )
    
    def test_create_service_request(self):
        """Test creating a service request"""
        request = ServiceRequest.objects.create(
            client=self.client_user,
            expert=self.expert_user,
            service=self.service,
            title='Need Paris Tour',
            description='I need a guided tour of Paris'
        )
        self.assertEqual(request.client, self.client_user)
        self.assertEqual(request.expert, self.expert_user)
        self.assertEqual(request.service, self.service)
        self.assertEqual(request.status, 'new')
        self.assertEqual(request.priority, 'medium')
    
    def test_service_request_str(self):
        """Test string representation of service request"""
        request = ServiceRequest.objects.create(
            client=self.client_user,
            title='Need Paris Tour',
            description='I need a guided tour of Paris'
        )
        expected = f"Need Paris Tour - {self.client_user.name} {self.client_user.first_name}"
        self.assertEqual(str(request), expected)


class MessageModelTest(TestCase):
    """Test the Message model"""
    
    def setUp(self):
        self.client_user = User.objects.create_user(
            email='client@example.com',
            password='testpass123',
            name='Client',
            first_name='User',
            account_type='client'
        )
        self.service_request = ServiceRequest.objects.create(
            client=self.client_user,
            title='Test Request',
            description='Test description'
        )
    
    def test_create_message(self):
        """Test creating a message"""
        message = Message.objects.create(
            service_request=self.service_request,
            sender=self.client_user,
            content='Hello, I need help with this request'
        )
        self.assertEqual(message.service_request, self.service_request)
        self.assertEqual(message.sender, self.client_user)
        self.assertEqual(message.content, 'Hello, I need help with this request')
        self.assertFalse(message.is_read)


class DocumentModelTest(TestCase):
    """Test the Document model"""
    
    def setUp(self):
        self.client_user = User.objects.create_user(
            email='client@example.com',
            password='testpass123',
            name='Client',
            first_name='User',
            account_type='client'
        )
        self.service_request = ServiceRequest.objects.create(
            client=self.client_user,
            title='Test Request',
            description='Test description'
        )
    
    def test_create_document(self):
        """Test creating a document"""
        document = Document.objects.create(
            service_request=self.service_request,
            name='Test Document',
            document_type='identity',
            uploaded_by=self.client_user
        )
        self.assertEqual(document.service_request, self.service_request)
        self.assertEqual(document.name, 'Test Document')
        self.assertEqual(document.document_type, 'identity')
        self.assertEqual(document.uploaded_by, self.client_user)
        self.assertEqual(document.status, 'pending')


class RendezVousModelTest(TestCase):
    """Test the RendezVous model"""
    
    def setUp(self):
        self.client_user = User.objects.create_user(
            email='client@example.com',
            password='testpass123',
            name='Client',
            first_name='User',
            account_type='client'
        )
        self.expert_user = User.objects.create_user(
            email='expert@example.com',
            password='testpass123',
            name='Expert',
            first_name='User',
            account_type='expert'
        )
        self.service_request = ServiceRequest.objects.create(
            client=self.client_user,
            title='Test Request',
            description='Test description'
        )
    
    def test_create_rendezvous(self):
        """Test creating a rendez-vous"""
        rdv = RendezVous.objects.create(
            service_request=self.service_request,
            client=self.client_user,
            expert=self.expert_user,
            date=date.today(),
            start_time=datetime.now().time(),
            duration_minutes=60,
            location='Office'
        )
        self.assertEqual(rdv.service_request, self.service_request)
        self.assertEqual(rdv.client, self.client_user)
        self.assertEqual(rdv.expert, self.expert_user)
        self.assertEqual(rdv.status, 'pending')


class ContactMessageModelTest(TestCase):
    """Test the ContactMessage model"""
    
    def test_create_contact_message(self):
        """Test creating a contact message"""
        message = ContactMessage.objects.create(
            name='John Doe',
            email='john@example.com',
            subject='Question about services',
            message='I have a question about your services'
        )
        self.assertEqual(message.name, 'John Doe')
        self.assertEqual(message.email, 'john@example.com')
        self.assertEqual(message.subject, 'Question about services')
        self.assertFalse(message.is_replied)


class CustomRequestViewTest(TestCase):
    """Test custom request views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test',
            first_name='User'
        )
    
    def test_contact_view(self):
        """Test contact view"""
        response = self.client.get(reverse('custom_requests:contact'))
        self.assertEqual(response.status_code, 200)
    
    def test_authenticated_user_dashboard(self):
        """Test authenticated user can access dashboard"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('custom_requests:dashboard'))
        self.assertEqual(response.status_code, 200)
