from django.conf import settings
from .models import Category


def site_settings(request):
    """Глобальные настройки сайта для шаблонов"""
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'Forum Community'),
        'forum_categories': Category.objects.filter(is_active=True),
    }
