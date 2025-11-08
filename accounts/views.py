from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model

from .forms import SignupForm, UserUpdateForm, ProfileUpdateForm
from .models import UserProfile

User = get_user_model()


def signup(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('forum:index')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('forum:index')
    else:
        form = SignupForm()
    
    return render(request, 'accounts/signup.html', {'form': form})


def profile(request, username):
    """Просмотр профиля пользователя"""
    user = get_object_or_404(User, username=username)
    
    # Создать профиль если не существует
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    context = {
        'profile_user': user,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    """Редактирование профиля"""
    # Создать профиль если не существует
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль обновлен')
            return redirect('accounts:profile', username=request.user.username)
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile_edit.html', context)
