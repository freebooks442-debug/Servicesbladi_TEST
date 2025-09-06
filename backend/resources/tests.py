from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from resources.models import Resource

User = get_user_model()


class ResourceModelTest(TestCase):
    """Test the Resource model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            name='Admin',
            first_name='User',
            account_type='admin'
        )
    
    def test_create_resource(self):
        """Test creating a resource"""
        resource = Resource.objects.create(
            category='administrative',
            title='Sample Document',
            description='A sample document',
            created_by=self.user
        )
        self.assertEqual(resource.title, 'Sample Document')
        self.assertEqual(resource.category, 'administrative')
        self.assertEqual(resource.created_by, self.user)
        self.assertTrue(resource.is_active)
        self.assertEqual(resource.view_count, 0)
        self.assertEqual(resource.download_count, 0)
    
    def test_resource_str_representation(self):
        """Test string representation of resource"""
        resource = Resource.objects.create(
            category='tourism',
            title='Travel Guide',
            description='A travel guide',
            created_by=self.user
        )
        expected = f"Travel Guide (Tourism)"
        self.assertEqual(str(resource), expected)


class ResourceViewTest(TestCase):
    """Test resource views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test',
            first_name='User'
        )
    
    def test_resource_list_view(self):
        """Test resource list view"""
        response = self.client.get(reverse('resources:resource_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_authenticated_user_can_access_resources(self):
        """Test authenticated user can access resources"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('resources:resource_list'))
        self.assertEqual(response.status_code, 200)
