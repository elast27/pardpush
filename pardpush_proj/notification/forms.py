import psycopg2
import os
from twilio.rest import Client
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError

from notification.models import (Student, Tag, User, Event)

from django.core import mail
from django.core.mail import send_mail, EmailMessage

class OrganizerSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_organizer = True
        if commit:
            user.save()
        return user


class StudentSignUpForm(UserCreationForm):
    # Email field
    email = forms.EmailField(required=True, help_text='Must be a valid lafayette.edu or gmail account.')
    phone = forms.CharField(required=True)
    
    interests = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_student = True
        user.email = self.cleaned_data["email"]
        user.save()
        student = Student.objects.create(user=user)
        student.interests.add(*self.cleaned_data.get('interests'))
        student.phone=self.cleaned_data["phone"]
        student.save()
        return user


class StudentInterestsForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('interests', )
        widgets = {
            'interests': forms.CheckboxSelectMultiple
        }

class DateForm(forms.Form):
    date = forms.DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control datetimepicker-input',
            'data-target': '#datetimepicker1'
        })
    )

class TagSelectForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ('name', 'tag', 'date', 'location', 'message', )
        widgets = {
            'tag': forms.CheckboxSelectMultiple,
            'data': DateForm,
        }
        
    # Method for sending email notifications to users
    def send_notification(self, request, queryset):
        connection = mail.get_connection()

        for obj in User.objects.all():
            field_name = 'is_student'
            field_object = User._meta.get_field(field_name)
            field_value = getattr(obj, field_object.attname)
            
            if(str(field_value) == "True"):
                field_name = 'email'
                field_object = User._meta.get_field(field_name)
                field_value = getattr(obj, field_object.attname)
                
                # Construct the body of the email
                email = EmailMessage(
                            queryset.cleaned_data['name'],
                            'Event Date: ' + str(queryset.cleaned_data['date']) + '\n' 
                            + 'Event Location: ' + queryset.cleaned_data['location'] + '\n'
                            + '\n' + queryset.cleaned_data['message'], 
                            'pardpushhost@gmail.com', # Host gmail
                            [str(field_value)], # Recepient
                    )
                email.send()
                
        connection.close()

    def send_SMS(self, request, queryset):
        def createQuery(lst):
            query = 'SELECT phone FROM usable_table WHERE tagname='
            if len(lst)==1:
                query += '\'' + lst[0].__str__() + '\''
            else:
                for i in range(0, len(lst)-1):
                    query += '\'' + lst[i].__str__()+'\' OR tagname='
                query += '\'' + lst[-1].__str__() + '\''
                query += " GROUP BY phone"
            return query
        def sendQuery(query):
            conn = psycopg2.connect("dbname=pardpush user=matthewstern")
            cur = conn.cursor()
            cur.execute(query)
            lst = cur.fetchall()
            cur.close()
            conn.close()
            return lst
        def sendLoop(lst, msg):
            #SECURE
            #account_sid = os.environ['TWILIO_ACCOUNT_SID']
            #auth_token = os.environ['TWILIO_AUTH_TOKEN']
            #TEST
            #account_sid = 'AC65adbf73953668e75fc8dea6e776a18a'
            #auth_token = '3890a907679e2a2402c5595bfa576f14'
            #REAL BELOW
            account_sid = 'AC2deef53dadb3d1035219e6f346544e98'
            auth_token = 'd437bf9f8e7dc2602dd5632d62062810'
            client = Client(account_sid, auth_token)
            for i in lst:
                message = client.messages.create(
                    from_='+16108105091',
                    body=msg,
                    to=i
                )
        tags = list(queryset.cleaned_data['tag'])
        msg = queryset.cleaned_data['name'] + ": " + queryset.cleaned_data['date'].__str__() + " @ " + queryset.cleaned_data['location'] + "\n" + queryset.cleaned_data['message']
        query = createQuery(tags)
        lst = sendQuery(query)
        sendLoop(lst,msg)