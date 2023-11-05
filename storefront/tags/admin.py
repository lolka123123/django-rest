from django.contrib import admin
from . import models

# Register your models here.

@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'label']
    list_display_links = ['label']

@admin.register(models.TaggedItem)
class TaggedItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'tag', 'content_object']
    list_display_links = ['id', 'tag']