from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from services.models import ServiceCategory, ServiceType, Service, TourismService, AdministrativeService
from accounts.models import Expert
from decimal import Decimal
from datetime import timedelta

User = get_user_model()


class ServiceCategoryModelTest(TestCase):
    """Test the ServiceCategory model"""
    
    def test_create_category(self):
        """Test creating a service category"""
        category = ServiceCategory.objects.create(
            name='Tourism',
            description='Tourism services',
            slug='tourism'
        )
        self.assertEqual(category.name, 'Tourism')
        self.assertEqual(category.description, 'Tourism services')
        self.assertEqual(category.slug, 'tourism')
    
    def test_category_str_representation(self):
        """Test the string representation of category"""
        category = ServiceCategory.objects.create(
            name='Tourism',
            slug='tourism'
        )
        self.assertEqual(str(category), 'Tourism')


class ServiceTypeModelTest(TestCase):
    """Test the ServiceType model"""
    
    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name='Tourism',
            slug='tourism'
        )
    
    def test_create_service_type(self):
        """Test creating a service type"""
        service_type = ServiceType.objects.create(
            category=self.category,
            name='City Tours',
            description='Guided city tours',
            price=Decimal('50.00')
        )
        self.assertEqual(service_type.name, 'City Tours')
        self.assertEqual(service_type.category, self.category)
        self.assertEqual(service_type.price, Decimal('50.00'))


class ServiceModelTest(TestCase):
    """Test the Service model"""
    
    def setUp(self):
        # Create a user for expert
        self.user = User.objects.create_user(
            email='expert@example.com',
            password='testpass123',
            name='Expert',
            first_name='User',
            account_type='expert'
        )
        self.expert = Expert.objects.create(
            user=self.user,
            specialization='Tourism',
            experience_years=5
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
    
    def test_create_service(self):
        """Test creating a service"""
        service = Service.objects.create(
            service_type=self.service_type,
            title='Paris City Tour',
            description='Guided tour of Paris',
            price=Decimal('75.00'),
            duration=timedelta(hours=4),
            expert=self.expert
        )
        self.assertEqual(service.title, 'Paris City Tour')
        self.assertEqual(service.service_type, self.service_type)
        self.assertEqual(service.expert, self.expert)
        self.assertEqual(service.price, Decimal('75.00'))
    
    def test_service_str_representation(self):
        """Test the string representation of service"""
        service = Service.objects.create(
            service_type=self.service_type,
            title='Paris City Tour',
            description='Guided tour of Paris',
            price=Decimal('75.00')
        )
        self.assertEqual(str(service), 'Paris City Tour')


class TourismServiceModelTest(TestCase):
    """Test the TourismService model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='expert@example.com',
            password='testpass123',
            name='Expert',
            first_name='User',
            account_type='expert'
        )
        self.expert = Expert.objects.create(
            user=self.user,
            specialization='Tourism',
            experience_years=5
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
    
    def test_create_tourism_service(self):
        """Test creating a tourism service"""
        service = TourismService.objects.create(
            service_type=self.service_type,
            title='Paris City Tour',
            description='Guided tour of Paris',
            price=Decimal('75.00'),
            location='Paris',
            includes_transport=True,
            group_size=8
        )
        self.assertEqual(service.location, 'Paris')
        self.assertTrue(service.includes_transport)
        self.assertEqual(service.group_size, 8)


class ServiceViewTest(TestCase):
    """Test service-related views"""
    
    def setUp(self):
        self.client = Client()
        self.category = ServiceCategory.objects.create(
            name='Tourism',
            slug='tourism'
        )
        self.service_type = ServiceType.objects.create(
            category=self.category,
            name='City Tours',
            price=Decimal('50.00')
        )
        
    def test_service_list_view(self):
        """Test service list view"""
        response = self.client.get(reverse('services:service_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_service_category_view(self):
        """Test service category view"""
        response = self.client.get(reverse('services:services_by_category', args=[self.category.slug]))
        self.assertEqual(response.status_code, 200)
