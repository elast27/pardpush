from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe
from datetime import datetime
from phone_field import PhoneField


class User(AbstractUser):
    budget = models.FloatField(default=0, verbose_name='budget')
    is_student = models.BooleanField(default=False)
    is_organizer = models.BooleanField(default=False)
    


class Tag(models.Model):
    tagname = models.CharField(max_length=30)
    color = models.CharField(max_length=7, default='#007bff')

    def __str__(self):
        return self.tagname

    def get_html_badge(self):
        name = escape(self.tagname)
        color = escape(self.color)
        html = '<span class="badge badge-pill badge-primary" style="background-color: %s">%s</span>' % (color, name)
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
    phone = PhoneField(blank=True, verbose_name='phone')
    sms_unsub = models.BooleanField(default=False)
    email_unsub = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

###Materialized Views###

class UsableTable(models.Model):
    phone = models.CharField(max_length=31)
    email = models.CharField(max_length=254)
    tagname = models.CharField(max_length=30)
    email_unsub = models.BooleanField()
    sms_unsub = models.BooleanField()
    
    class Meta:
        managed = False
        db_table = 'usabletable'

class StudentPhones(models.Model):
    user_id = models.IntegerField()
    phone = models.CharField(max_length=31)
    
    class Meta:
        managed = False
        db_table = 'studentphones'

class StudentsPerTag(models.Model):
    student_id = models.IntegerField()
    taglist = models.TextField()
    
    class Meta:
        managed = False
        db_table = 'studentspertag'

class EventTags(models.Model):
    event_id = models.IntegerField()
    tagname = models.TextField()
    
    class Meta:
        managed = False
        db_table = 'eventtags'