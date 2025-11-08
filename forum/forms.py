from django import forms
from .models import Thread, Post, Report, PrivateMessage


class ThreadForm(forms.ModelForm):
    """Форма создания темы"""
    
    class Meta:
        model = Thread
        fields = ('title', 'category', 'content', 'tags')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок темы'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Содержание темы (поддерживается Markdown)'}),
        }


class PostForm(forms.ModelForm):
    """Форма создания сообщения"""
    
    class Meta:
        model = Post
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Ваше сообщение (поддерживается Markdown)'}),
        }


class ReportForm(forms.ModelForm):
    """Форма жалобы на сообщение"""
    
    class Meta:
        model = Report
        fields = ('report_type', 'description')
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Опишите причину жалобы'}),
        }


class PrivateMessageForm(forms.ModelForm):
    """Форма личного сообщения"""
    
    class Meta:
        model = PrivateMessage
        fields = ('recipient', 'subject', 'content')
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Тема сообщения'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Текст сообщения'}),
        }


class SearchForm(forms.Form):
    """Форма поиска"""
    q = forms.CharField(
        label='Поиск',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Поиск по форуму...'})
    )
    
    search_in = forms.ChoiceField(
        label='Искать в',
        choices=[
            ('all', 'Везде'),
            ('threads', 'Темы'),
            ('posts', 'Сообщения'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
