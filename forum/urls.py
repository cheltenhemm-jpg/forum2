from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    # Главная и категории
    path('', views.index, name='index'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # Темы
    path('thread/<slug:slug>/', views.thread_detail, name='thread_detail'),
    path('thread/create/', views.thread_create, name='thread_create'),
    path('thread/<slug:slug>/edit/', views.thread_edit, name='thread_edit'),
    
    # Сообщения
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/like/', views.post_like, name='post_like'),
    path('post/<int:pk>/report/', views.post_report, name='post_report'),
    
    # Поиск
    path('search/', views.search, name='search'),
    
    # Личные сообщения
    path('messages/', views.messages_inbox, name='messages_inbox'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    path('messages/send/', views.message_send, name='message_send'),
    path('messages/send/<str:username>/', views.message_send, name='message_send_to'),
]
