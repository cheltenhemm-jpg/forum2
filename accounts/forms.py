from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, UserProfile


class SignupForm(forms.ModelForm):
    """Форма регистрации пользователя"""
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('username', 'email')
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают')
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            # Create profile
            UserProfile.objects.create(user=user)
        return user


class UserUpdateForm(forms.ModelForm):
    """Форма обновления профиля пользователя"""
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'bio', 'location', 'website', 'avatar', 'signature')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'signature': forms.Textarea(attrs={'rows': 2}),
        }


class ProfileUpdateForm(forms.ModelForm):
    """Форма обновления дополнительной информации профиля"""
    
    class Meta:
        model = UserProfile
        fields = ('phone', 'telegram', 'discord', 'birthday', 'gender', 'show_email', 'email_notifications')
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
        }
