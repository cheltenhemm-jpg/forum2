from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'reputation', 'post_count', 'is_banned', 'date_joined')
    list_filter = ('role', 'is_banned', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'avatar', 'bio', 'location', 'website', 'reputation', 
                      'post_count', 'thread_count', 'is_banned', 'ban_reason', 'signature')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('email', 'role')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'telegram', 'birthday', 'email_notifications')
    search_fields = ('user__username', 'phone', 'telegram')
    raw_id_fields = ('user',)
