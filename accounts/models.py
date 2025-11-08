from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from PIL import Image


class User(AbstractUser):
    """Расширенная модель пользователя"""
    
    ROLE_CHOICES = (
        ('user', 'Пользователь'),
        ('moderator', 'Модератор'),
        ('admin', 'Администратор'),
    )
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    reputation = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    thread_count = models.IntegerField(default=0)
    last_seen = models.DateTimeField(auto_now=True)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True)
    signature = models.TextField(max_length=200, blank=True)
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize avatar if it exists
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.avatar.path)
    
    def is_moderator(self):
        return self.role in ['moderator', 'admin']
    
    def is_admin_user(self):
        return self.role == 'admin'
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def update_stats(self):
        """Обновление статистики пользователя"""
        from forum.models import Thread, Post
        self.thread_count = Thread.objects.filter(author=self).count()
        self.post_count = Post.objects.filter(author=self).count()
        self.save()


class UserProfile(models.Model):
    """Дополнительная информация профиля пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    telegram = models.CharField(max_length=100, blank=True)
    discord = models.CharField(max_length=100, blank=True)
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Мужской'), ('F', 'Женский'), ('O', 'Другой')], blank=True)
    show_email = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f"Profile of {self.user.username}"
