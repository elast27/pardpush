import psycopg2
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError

from notification.models import (Student, Tag, User, Event)
from django.core.mail import send_mass_mail

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

    def send_initSMS(self, request, queryset):
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
        def getStudentNumber(id):
            conn = psycopg2.connect('dbname=pardpush user=dbadmin')
            cur = conn.cursor()
            id = request.user.id
            cur.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY studentphones;')
            conn.commit()
            cur.execute('SELECT phone FROM studentphones WHERE user_id='+id.__str__()+';')
            tmp = cur.fetchone()
            cur.close()
            conn.close()
            return tmp
        msg = 'Welcome to PardPush, ' + request.user.first_name + '! Visit the user dashboard at pardpush.cs.lafayette.edu to change your preferences, or reply STOP to unsubscribe at any time. Msg&Data Rates May Apply.'
        num = getStudentNumber(request.user.id)
        try:
            message = client.messages.create(
                from_='+16108105091',
                body=msg,
                to=num[0]
            )
        except TwilioRestException:
            #maybe do something about the person that unsubscribed here
            print(i.__str__() + " unsubscribed; no message sent")

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
        def createQuery(lst):
            query = 'SELECT email FROM usabletable WHERE tagname='
            if len(lst)==1:
                query += '\'' + lst[0].__str__() + '\''
            else:
                for i in range(0, len(lst)-1):
                    query += '\'' + lst[i].__str__()+'\' OR tagname='
                query += '\'' + lst[-1].__str__() + '\''
                query += " GROUP BY email"
            return query
        def sendQuery(query):
            conn = psycopg2.connect("dbname=pardpush user=dbadmin")
            cur = conn.cursor()
            cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY usabletable;")
            conn.commit()
            cur.execute(query)
            lst = cur.fetchall()
            cur.close()
            conn.close()
            return lst
        tags = list(queryset.cleaned_data['tag'])
        msg = queryset.cleaned_data['name'] + ": " + queryset.cleaned_data['date'].strftime('%a, %b %d, %-I:%M %p') + " @ " + queryset.cleaned_data['location'] + "\n" + queryset.cleaned_data['message']
        query = createQuery(tags)
        lst = sendQuery(query)
        subject = 'PardPush: ' + queryset.cleaned_data['name']
        body = 'New PardPush notification! \n Event Date: ' + str(queryset.cleaned_data['date'].strftime('%a, %b %d, %-I:%M %p')) + '\n' + 'Event Location: ' + queryset.cleaned_data['location'] + '\n' + 'Details: ' + queryset.cleaned_data['message']
        msgs = [(subject,body,'pardpushhost@gmail.com',recipient) for recipient in lst] #hides recipient list from each recipient
        send_mass_mail(msgs,fail_silently=True)

    def send_SMS(self, request, queryset):
        def createQuery(lst):
            query = 'SELECT phone FROM usabletable WHERE tagname='
            if len(lst)==1:
                query += '\'' + lst[0].__str__() + '\''
            else:
                for i in range(0, len(lst)-1):
                    query += '\'' + lst[i].__str__()+'\' OR tagname='
                query += '\'' + lst[-1].__str__() + '\''
                query += " GROUP BY phone"
            return query
        def sendQuery(query):
            conn = psycopg2.connect("dbname=pardpush user=dbadmin")
            cur = conn.cursor()
            cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY usabletable;")
            conn.commit()
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
                try:
                    message = client.messages.create(
                        from_='+16108105091',
                        body=msg,
                        to=i
                    )
                except TwilioRestException:
                    #maybe do something about the person that unsubscribed here
                    print(i.__str__() + " unsubscribed; no message sent")
        def getBudget(request):
            conn = psycopg2.connect('dbname=pardpush user=dbadmin')
            cur = conn.cursor()
            id = request.user.id
            cur.execute('SELECT budget FROM notification_user WHERE id='+id.__str__()+';')
            tmp = cur.fetchone()
            cur.close()
            conn.close()
            return tmp
        def setBudget(request,val):
            conn = psycopg2.connect('dbname=pardpush user=dbadmin')
            cur = conn.cursor()
            id = request.user.id
            cur.execute('UPDATE notification_user SET budget=' + val.__str__() + ' where id=' + id.__str__() + ';')
            conn.commit()
            cur.close()
            conn.close()
        tags = list(queryset.cleaned_data['tag'])
        msg = queryset.cleaned_data['name'] + ": " + queryset.cleaned_data['date'].strftime('%a, %b %d, %-I:%M %p') + " @ " + queryset.cleaned_data['location'] + "\n" + queryset.cleaned_data['message']
        query = createQuery(tags)
        lst = sendQuery(query)
        cost = len(lst) * .00562
        budget = getBudget(request)
        if cost <= budget[0]:
            sendLoop(lst,msg)
            setBudget(request,budget[0]-cost)
            return (True,cost)
        else:
            return (False,cost)