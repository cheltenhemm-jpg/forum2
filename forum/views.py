from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone

from .models import Category, Thread, Post, Like, Report, PrivateMessage
from .forms import ThreadForm, PostForm, ReportForm, PrivateMessageForm, SearchForm


def index(request):
    """Главная страница форума"""
    categories = Category.objects.filter(is_active=True).prefetch_related('threads')
    recent_threads = Thread.objects.filter(is_active=True).select_related('author', 'category').order_by('-updated_at')[:10]
    
    # Статистика
    stats = {
        'total_threads': Thread.objects.filter(is_active=True).count(),
        'total_posts': Post.objects.filter(is_active=True).count(),
        'total_users': settings.AUTH_USER_MODEL and __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model().objects.count() or 0,
    }
    
    context = {
        'categories': categories,
        'recent_threads': recent_threads,
        'stats': stats,
    }
    return render(request, 'forum/index.html', context)


def category_detail(request, slug):
    """Просмотр категории с темами"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    threads_list = category.threads.filter(is_active=True).select_related('author').order_by('-is_pinned', '-updated_at')
    
    # Пагинация
    paginator = Paginator(threads_list, settings.THREADS_PER_PAGE)
    page = request.GET.get('page')
    threads = paginator.get_page(page)
    
    context = {
        'category': category,
        'threads': threads,
    }
    return render(request, 'forum/category_detail.html', context)


def thread_detail(request, slug):
    """Просмотр темы с сообщениями"""
    thread = get_object_or_404(Thread, slug=slug, is_active=True)
    posts_list = thread.posts.filter(is_active=True).select_related('author').prefetch_related('likes')
    
    # Увеличить счетчик просмотров
    thread.increment_views()
    
    # Пагинация
    paginator = Paginator(posts_list, settings.POSTS_PER_PAGE)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    # Форма ответа
    if request.method == 'POST' and request.user.is_authenticated and not thread.is_locked:
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.author = request.user
            post.save()
            messages.success(request, 'Сообщение добавлено')
            return redirect('forum:thread_detail', slug=thread.slug)
    else:
        form = PostForm()
    
    context = {
        'thread': thread,
        'posts': posts,
        'form': form,
    }
    return render(request, 'forum/thread_detail.html', context)


@login_required
def thread_create(request):
    """Создание новой темы"""
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.save()
            form.save_m2m()  # Сохранить теги
            messages.success(request, 'Тема создана успешно')
            return redirect('forum:thread_detail', slug=thread.slug)
    else:
        form = ThreadForm()
    
    context = {'form': form}
    return render(request, 'forum/thread_create.html', context)


@login_required
def thread_edit(request, slug):
    """Редактирование темы"""
    thread = get_object_or_404(Thread, slug=slug)
    
    # Проверка прав
    if thread.author != request.user and not request.user.is_moderator():
        messages.error(request, 'У вас нет прав для редактирования этой темы')
        return redirect('forum:thread_detail', slug=thread.slug)
    
    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тема обновлена')
            return redirect('forum:thread_detail', slug=thread.slug)
    else:
        form = ThreadForm(instance=thread)
    
    context = {'form': form, 'thread': thread}
    return render(request, 'forum/thread_edit.html', context)


@login_required
def post_edit(request, pk):
    """Редактирование сообщения"""
    post = get_object_or_404(Post, pk=pk)
    
    # Проверка прав
    if post.author != request.user and not request.user.is_moderator():
        messages.error(request, 'У вас нет прав для редактирования этого сообщения')
        return redirect('forum:thread_detail', slug=post.thread.slug)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.is_edited = True
            post.edited_at = timezone.now()
            post.save()
            messages.success(request, 'Сообщение обновлено')
            return redirect('forum:thread_detail', slug=post.thread.slug)
    else:
        form = PostForm(instance=post)
    
    context = {'form': form, 'post': post}
    return render(request, 'forum/post_edit.html', context)


@login_required
@require_POST
def post_like(request, pk):
    """Лайк/дизлайк сообщения"""
    post = get_object_or_404(Post, pk=pk)
    like_type = int(request.POST.get('type', 1))
    
    # Проверить существующий лайк
    existing_like = Like.objects.filter(post=post, user=request.user).first()
    
    if existing_like:
        if existing_like.like_type == like_type:
            # Убрать лайк
            existing_like.delete()
            action = 'removed'
        else:
            # Изменить тип лайка
            existing_like.like_type = like_type
            existing_like.save()
            action = 'changed'
    else:
        # Создать новый лайк
        Like.objects.create(post=post, user=request.user, like_type=like_type)
        action = 'added'
    
    # Подсчитать лайки
    likes_count = Like.objects.filter(post=post, like_type=1).count()
    dislikes_count = Like.objects.filter(post=post, like_type=-1).count()
    
    return JsonResponse({
        'action': action,
        'likes': likes_count,
        'dislikes': dislikes_count,
    })


@login_required
def post_report(request, pk):
    """Жалоба на сообщение"""
    post = get_object_or_404(Post, pk=pk)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.post = post
            report.reporter = request.user
            report.save()
            messages.success(request, 'Жалоба отправлена модераторам')
            return redirect('forum:thread_detail', slug=post.thread.slug)
    else:
        form = ReportForm()
    
    context = {'form': form, 'post': post}
    return render(request, 'forum/post_report.html', context)


def search(request):
    """Поиск по форуму"""
    form = SearchForm(request.GET)
    results = []
    query = None
    
    if form.is_valid():
        query = form.cleaned_data.get('q')
        search_in = form.cleaned_data.get('search_in', 'all')
        
        if query:
            if search_in in ['all', 'threads']:
                threads = Thread.objects.filter(
                    Q(title__icontains=query) | Q(content__icontains=query),
                    is_active=True
                ).select_related('author', 'category')[:20]
                results.extend([('thread', t) for t in threads])
            
            if search_in in ['all', 'posts']:
                posts = Post.objects.filter(
                    content__icontains=query,
                    is_active=True
                ).select_related('author', 'thread')[:20]
                results.extend([('post', p) for p in posts])
    
    context = {
        'form': form,
        'results': results,
        'query': query,
    }
    return render(request, 'forum/search.html', context)


@login_required
def messages_inbox(request):
    """Входящие сообщения"""
    messages_list = request.user.received_messages.all().select_related('sender')
    
    paginator = Paginator(messages_list, 20)
    page = request.GET.get('page')
    messages_page = paginator.get_page(page)
    
    context = {'messages': messages_page}
    return render(request, 'forum/messages_inbox.html', context)


@login_required
def message_detail(request, pk):
    """Просмотр личного сообщения"""
    message = get_object_or_404(PrivateMessage, pk=pk)
    
    # Проверка прав
    if message.recipient != request.user and message.sender != request.user:
        messages.error(request, 'У вас нет доступа к этому сообщению')
        return redirect('forum:messages_inbox')
    
    # Отметить как прочитанное
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.read_at = timezone.now()
        message.save()
    
    context = {'message': message}
    return render(request, 'forum/message_detail.html', context)


@login_required
def message_send(request, username=None):
    """Отправка личного сообщения"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    recipient = None
    if username:
        recipient = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        form = PrivateMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            messages.success(request, 'Сообщение отправлено')
            return redirect('forum:messages_inbox')
    else:
        initial = {}
        if recipient:
            initial['recipient'] = recipient
        form = PrivateMessageForm(initial=initial)
    
    context = {'form': form, 'recipient': recipient}
    return render(request, 'forum/message_send.html', context)
