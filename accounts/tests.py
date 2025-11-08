from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserModelTest(TestCase):
    """Тесты модели пользователя"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Тест создания пользователя"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_default_role(self):
        """Тест роли пользователя по умолчанию"""
        self.assertEqual(self.user.role, 'user')
    
    def test_is_moderator_method(self):
        """Тест метода is_moderator"""
        self.assertFalse(self.user.is_moderator())
        self.user.role = 'moderator'
        self.assertTrue(self.user.is_moderator())
    
    def test_profile_creation(self):
        """Тест создания профиля"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertTrue(profile.email_notifications)
