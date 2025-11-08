from django.contrib import admin
from .models import Category, Thread, Post, Like, Attachment, Report, PrivateMessage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'views', 'is_pinned', 'is_locked', 'is_active', 'created_at')
    list_filter = ('category', 'is_pinned', 'is_locked', 'is_active', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    date_hierarchy = 'created_at'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'author', 'is_edited', 'is_active', 'created_at')
    list_filter = ('is_edited', 'is_active', 'created_at')
    search_fields = ('content', 'author__username', 'thread__title')
    raw_id_fields = ('thread', 'author')
    date_hierarchy = 'created_at'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'like_type', 'created_at')
    list_filter = ('like_type', 'created_at')
    search_fields = ('user__username',)
    raw_id_fields = ('post', 'user')


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'post', 'size', 'uploaded_at')
    search_fields = ('filename',)
    raw_id_fields = ('post',)
    date_hierarchy = 'uploaded_at'


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'reporter', 'report_type', 'status', 'moderator', 'created_at')
    list_filter = ('report_type', 'status', 'created_at')
    search_fields = ('description', 'reporter__username')
    raw_id_fields = ('post', 'reporter', 'moderator')
    date_hierarchy = 'created_at'


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('subject', 'sender__username', 'recipient__username')
    raw_id_fields = ('sender', 'recipient')
    date_hierarchy = 'created_at'
