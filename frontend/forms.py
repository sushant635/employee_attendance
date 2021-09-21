from django import forms
from django.contrib.auth.forms import UserCreationForm
from frontend.models import RegisterModel, PostModel
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from ckeditor.widgets import CKEditorWidget


class UserForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control m-2 data','placeholder':'Enter your username',}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control m-2 data','placeholder':"Enter Your Password",})) 
    class Meta:
        model = User
        fields = {'username','password'}

class UserProfileInfoForm(forms.ModelForm):
    employee_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control m-2 data','placeholder':'Enter your Employee code',}))
    class Meta():
        model = RegisterModel
        fields = {'employee_code'}


class PostForm(forms.ModelForm):
    post = forms.CharField(widget=CKEditorWidget())
    class Meta():
        model = PostModel
        fields = '__all__'
        
        