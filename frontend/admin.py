from django.contrib import admin
from frontend.models import RegisterModel,PostModel
# from django.contrib.auth.admin import UserAdmin

# Register your models here.
# class UserModel(UserAdmin):
    # pass

admin.site.register(RegisterModel)
admin.site.register(PostModel)
