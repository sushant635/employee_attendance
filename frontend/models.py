from django.db import models
from django.contrib.auth.models import User 
from ckeditor.fields import RichTextField
# Create your models here.


class RegisterModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_code = models.CharField(max_length=50)


    def __str__(self):
        return self.user.username


class PostModel(models.Model):
    post = RichTextField(blank=True,null=True)

    def __str__(self):
        return self.post