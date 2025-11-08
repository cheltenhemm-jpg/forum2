from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from taggit.managers import TaggableManager
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify


class Category(models.Model):
    """Категория форума"""
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField('Описание', blank=True)
    icon = models.CharField('Иконка', max_length=50, blank=True, help_text='Font Awesome класс')
    order = models.IntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активна', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('forum:category_detail', kwargs={'slug': self.slug})
    
    def thread_count(self):
        return self.threads.filter(is_active=True).count()
    
    def post_count(self):
        return sum(thread.posts.count() for thread in self.threads.filter(is_active=True))
    
    def last_post(self):
        posts = Post.objects.filter(thread__category=self, thread__is_active=True).order_by('-created_at')
        return posts.first() if posts.exists() else None


class Thread(models.Model):
    """Тема форума"""
    title = models.CharField('Заголовок', max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='threads', verbose_name='Категория')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='threads', verbose_name='Автор')
    content = MarkdownxField('Содержание')
    views = models.IntegerField('Просмотры', default=0)
    is_pinned = models.BooleanField('Закреплена', default=False)
    is_locked = models.BooleanField('Заблокирована', default=False)
    is_active = models.BooleanField('Активна', default=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)
    tags = TaggableManager(blank=True)
    
    class Meta:
        verbose_name = 'Тема'
        verbose_name_plural = 'Темы'
        ordering = ['-is_pinned', '-updated_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-updated_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        # Update author stats
        self.author.update_stats()
    
    def get_absolute_url(self):
        return reverse('forum:thread_detail', kwargs={'slug': self.slug})
    
    def formatted_markdown(self):
        return markdownify(self.content)
    
    def post_count(self):
        return self.posts.count()
    
    def last_post(self):
        return self.posts.order_by('-created_at').first()
    
    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])


class Post(models.Model):
    """Сообщение в теме"""
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='posts', verbose_name='Тема')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts', verbose_name='Автор')
    content = MarkdownxField('Содержание')
    is_edited = models.BooleanField('Отредактировано', default=False)
    edited_at = models.DateTimeField('Отредактировано в', null=True, blank=True)
    is_active = models.BooleanField('Активно', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Post by {self.author.username} in {self.thread.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update thread's updated_at
        self.thread.updated_at = self.created_at
        self.thread.save(update_fields=['updated_at'])
        # Update author stats
        self.author.update_stats()
    
    def formatted_markdown(self):
        return markdownify(self.content)
    
    def get_absolute_url(self):
        return f"{self.thread.get_absolute_url()}#post-{self.id}"


class Like(models.Model):
    """Лайк для сообщения"""
    LIKE_TYPES = (
        (1, 'Нравится'),
        (-1, 'Не нравится'),
    )
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    like_type = models.IntegerField(choices=LIKE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        unique_together = ('post', 'user')
    
    def __str__(self):
        return f"{self.user.username} -> {self.post.id} ({self.get_like_type_display()})"


class Attachment(models.Model):
    """Вложения к сообщениям"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'
    
    def __str__(self):
        return self.filename


class Report(models.Model):
    """Жалобы на сообщения"""
    REPORT_TYPES = (
        ('spam', 'Спам'),
        ('offensive', 'Оскорбление'),
        ('illegal', 'Незаконный контент'),
        ('other', 'Другое'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('reviewed', 'Рассмотрено'),
        ('resolved', 'Решено'),
        ('rejected', 'Отклонено'),
    )
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField('Описание')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_handled')
    moderator_note = models.TextField('Заметка модератора', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Жалоба'
        verbose_name_plural = 'Жалобы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report on post {self.post.id} by {self.reporter.username}"


class PrivateMessage(models.Model):
    """Личные сообщения"""
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField('Тема', max_length=200)
    content = MarkdownxField('Содержание')
    is_read = models.BooleanField('Прочитано', default=False)
    read_at = models.DateTimeField('Прочитано в', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Личное сообщение'
        verbose_name_plural = 'Личные сообщения'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.subject}"
    
    def formatted_markdown(self):
        return markdownify(self.content)
