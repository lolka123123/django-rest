from django.contrib import admin
from . import models


# Register your models here.


@admin.register(models.LikedItem)
class LikedItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'content_object']
    list_display_links = ['id', 'user']