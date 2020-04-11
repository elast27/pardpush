from django.contrib import admin

from notification.models import (Tag, User, Event)
from django.contrib.auth.models import Permission


class UserAdmin(admin.ModelAdmin):
    list_display = ('id','username', 'first_name','last_name', 'email','is_student', 'is_organizer', 'is_superuser')
    list_display_links = ('id','username')
    list_editable = ('is_student', 'is_organizer')
    list_filter = ('is_student', 'is_organizer','is_superuser')
    search_fields = ('first_name', 'last_name',)
    list_per_page = 25

admin.site.register(User, UserAdmin)

class TagAdmin(admin.ModelAdmin):
    list_display = ('id','name')
    list_display_links = ('id','name')
    search_fields = ('name',)
    list_per_page = 25

admin.site.register(Tag, TagAdmin)

class EventAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'owner', 'date','location',)
    list_display_links = ('id','name')
    search_fields = ('name', 'owner', 'tag')
    list_per_page = 25

admin.site.register(Event, EventAdmin)

admin.site.register(Permission)