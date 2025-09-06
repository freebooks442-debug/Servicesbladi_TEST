from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Utilisateur
from accounts.forms import UserEditForm, CustomPasswordChangeForm

User = get_user_model()


class UtilisateurModelTest(TestCase):
    """Test the custom User model"""
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = Utilisateur.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test',
            first_name='User'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test')
        self.assertEqual(user.first_name, 'User')
        self.assertEqual(user.account_type, 'client')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_verified)
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        user = Utilisateur.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            name='Admin',
            first_name='User'
        )
        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.account_type, 'admin')
        self.assertTrue(user.is_verified)


class UserEditFormTest(TestCase):
    """Test the UserEditForm"""
    
    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test',
            first_name='User'
        )
    
    def test_user_edit_form_valid(self):
        """Test user edit form with valid data"""
        form_data = {
            'name': 'Updated Name',
            'first_name': 'Updated First',
            'email': 'updated@example.com'
        }
        form = UserEditForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())


class AuthenticationViewTest(TestCase):
    """Test authentication views"""
    
    def setUp(self):
        self.client = Client()
        self.user = Utilisateur.objects.create_user(
            email='test@example.com',
            password='testpass123',
            name='Test',
            first_name='User'
        )
    
    def test_login_view_get(self):
        """Test login view GET request"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
