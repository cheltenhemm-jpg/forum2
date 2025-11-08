from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Category, Thread, Post, Like

User = get_user_model()


class ForumModelsTest(TestCase):
    """Тесты моделей форума"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='Test description'
        )
        self.thread = Thread.objects.create(
            title='Test Thread',
            slug='test-thread',
            category=self.category,
            author=self.user,
            content='Test content'
        )
    
    def test_category_creation(self):
        """Тест создания категории"""
        self.assertEqual(self.category.name, 'Test Category')
        self.assertTrue(self.category.is_active)
    
    def test_thread_creation(self):
        """Тест создания темы"""
        self.assertEqual(self.thread.title, 'Test Thread')
        self.assertEqual(self.thread.author, self.user)
        self.assertEqual(self.thread.category, self.category)
    
    def test_post_creation(self):
        """Тест создания сообщения"""
        post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='Test post content'
        )
        self.assertEqual(post.thread, self.thread)
        self.assertEqual(post.author, self.user)
    
    def test_thread_slug_generation(self):
        """Тест автогенерации slug"""
        thread = Thread.objects.create(
            title='New Thread',
            category=self.category,
            author=self.user,
            content='Content'
        )
        self.assertEqual(thread.slug, 'new-thread')


class ForumViewsTest(TestCase):
    """Тесты представлений форума"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.thread = Thread.objects.create(
            title='Test Thread',
            slug='test-thread',
            category=self.category,
            author=self.user,
            content='Test content'
        )
    
    def test_index_view(self):
        """Тест главной страницы"""
        response = self.client.get(reverse('forum:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Category')
    
    def test_category_detail_view(self):
        """Тест просмотра категории"""
        response = self.client.get(
            reverse('forum:category_detail', kwargs={'slug': self.category.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Thread')
    
    def test_thread_detail_view(self):
        """Тест просмотра темы"""
        response = self.client.get(
            reverse('forum:thread_detail', kwargs={'slug': self.thread.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Thread')
    
    def test_thread_create_requires_login(self):
        """Тест: создание темы требует авторизации"""
        response = self.client.get(reverse('forum:thread_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_thread_create_authenticated(self):
        """Тест создания темы авторизованным пользователем"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('forum:thread_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_post_creation_in_thread(self):
        """Тест создания поста в теме"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('forum:thread_detail', kwargs={'slug': self.thread.slug}),
            {'content': 'Test reply'}
        )
        self.assertEqual(Post.objects.filter(thread=self.thread).count(), 1)


class UserAuthenticationTest(TestCase):
    """Тесты аутентификации пользователей"""
    
    def setUp(self):
        self.client = Client()
    
    def test_user_registration(self):
        """Тест регистрации пользователя"""
        response = self.client.post(reverse('accounts:signup'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_user_login(self):
        """Тест входа пользователя"""
        User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class LikeSystemTest(TestCase):
    """Тесты системы лайков"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test',
            slug='test'
        )
        self.thread = Thread.objects.create(
            title='Test',
            slug='test',
            category=self.category,
            author=self.user,
            content='Content'
        )
        self.post = Post.objects.create(
            thread=self.thread,
            author=self.user,
            content='Post content'
        )
    
    def test_like_creation(self):
        """Тест создания лайка"""
        like = Like.objects.create(
            post=self.post,
            user=self.user,
            like_type=1
        )
        self.assertEqual(like.like_type, 1)
        self.assertEqual(Like.objects.filter(post=self.post).count(), 1)
    
    def test_unique_like_per_user(self):
        """Тест уникальности лайка от одного пользователя"""
        Like.objects.create(post=self.post, user=self.user, like_type=1)
        with self.assertRaises(Exception):
            Like.objects.create(post=self.post, user=self.user, like_type=1)
