from django.contrib import admin
from . import models

# Register your models here.

@admin.register(models.User)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'username']
    list_filter = ['id', 'username']
