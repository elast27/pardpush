from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe
from datetime import datetime


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_organizer = models.BooleanField(default=False)


class Tag(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default='#007bff')

    def __str__(self):
        return self.name

    def get_html_badge(self):
        name = escape(self.name)
        color = escape(self.color)
        html = '<span class="badge badge-primary" style="background-color: %s">%s</span>' % (color, name)
        return mark_safe(html)

class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=255)
    tag = models.ManyToManyField(Tag, related_name='event_tags')
    date = models.DateTimeField(default=datetime.now, blank=True)
    location = models.CharField(max_length=255)
    message = models.TextField(default='', blank=True)

    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    interests = models.ManyToManyField(Tag, related_name='interested_students')
    phone = models.CharField(blank=True, max_length = 254, verbose_name='phone')

    def __str__(self):
        return self.user.username
