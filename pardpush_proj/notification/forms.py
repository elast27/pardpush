import psycopg2
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError
from tempus_dominus.widgets import DateTimePicker

from notification.models import (Student, Tag, User, Event)
from django.core.mail import send_mass_mail,send_mail

from django_redis import get_redis_connection
from rq_scheduler import Scheduler
from datetime import datetime,timedelta,timezone


class OrganizerSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_organizer = True
        if commit:
            user.save()
        return user


class StudentSignUpForm(forms.ModelForm):
    # Email field
    #email = forms.EmailField(required=True, help_text='Must be a valid lafayette.edu or gmail account.')
    
    
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
            conn = psycopg2.connect("dbname='pardpush' user='pardpushs'")
            cur = conn.cursor()
            id = request.user.id
            cur.execute('REFRESH MATERIALIZED VIEW studentphones;')
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

    class Meta:
        model = User
        fields = ('phone', 'interests', )

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.save()
        student = Student.objects.create(user=user)
        student.interests.add(*self.cleaned_data.get('interests'))
        student.phone=self.cleaned_data["phone"]
        student.save()
        return user


class StudentInterestsForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('interests', 'email_unsub', 'sms_unsub',)
        widgets = {
            'interests': forms.CheckboxSelectMultiple,
            'email_unsub': forms.CheckboxInput,
            'sms_unsub': forms.CheckboxInput,
        }

class DateForm(forms.Form):
    date = forms.DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'], 
        widget=DateTimePicker()
    )

class TagSelectForm(forms.ModelForm):
    date = forms.DateTimeField(
        input_formats=['%m/%d/%Y %H:%M %p'], 
        widget=DateTimePicker(
            options={
                'useCurrent': True,
                'collapse': False,
            },
            attrs={
                'append': 'fa fa-calendar',
                'icon_toggle': True,
            }
        )
    )
    #delta = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'0','min':'0','max': '60','type': 'number'}))
    #timeunit = forms.CharField(widget=forms.Select(attrs={'class':'form-control'},choices=(('1','minutes'),('2','hours'),('3','days'))))
    #shift = forms.CharField(widget=forms.Select(attrs={'class':'form-control'},choices=(('1','before'),('2','after'))))
    class Meta:
        model = Event
        #fields = ('name', 'tag', 'date', 'delta', 'timeunit', 'shift', 'location', 'message', )
        fields = ('name', 'tag', 'date', 'location', 'message', )
        widgets = {
            'tag': forms.CheckboxSelectMultiple,
        }
        
    # Method for sending email notifications to users
    def send_notification(self, request, queryset):
        def createQuery(lst):
            query = 'SELECT email FROM usabletable WHERE (tagname='
            if len(lst)==1:
                query += "\'" + lst[0].__str__() + "\') AND (email_unsub='f') GROUP BY email;"
            else:
                for i in range(0, len(lst)-1):
                    query += '\'' + lst[i].__str__()+'\' OR tagname='
                query += '\'' + lst[-1].__str__() + '\''
                query += ") AND (email_unsub='f') GROUP BY email;"
            return query
        def sendQuery(query):
            conn = psycopg2.connect("dbname=pardpush user=pardpushs")
            cur = conn.cursor()
            cur.execute("REFRESH MATERIALIZED VIEW usabletable;")
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
        msgs = [(subject,body,'PardPush <pardpushhost@gmail.com>',recipient) for recipient in lst] #hides recipient list from each recipient
        send_mass_mail(msgs,fail_silently=True)

    def send_SMS(self, request, queryset):
        def createQuery(lst):
            query = 'SELECT phone FROM usabletable WHERE (tagname='
            if len(lst)==1:
                query += "\'" + lst[0].__str__() + "\') AND (sms_unsub='f') GROUP BY phone;"
            else:
                for i in range(0, len(lst)-1):
                    query += '\'' + lst[i].__str__()+'\' OR tagname='
                query += '\'' + lst[-1].__str__() + '\''
                query += ") AND (sms_unsub='f') GROUP BY phone;"
            return query
        def sendQuery(query):
            conn = psycopg2.connect("dbname=pardpush user=pardpushs")
            cur = conn.cursor()
            cur.execute("REFRESH MATERIALIZED VIEW usabletable;")
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
                    #stu = Student.objects.filter(phone=i[0]).update(sms_unsub=True) #enable this in the future when implementation for "Start" sms response is done
                    print(i.__str__() + " unsubscribed; no message sent")
        def getBudget(request):
            conn = psycopg2.connect('dbname=pardpush user=pardpushs')
            cur = conn.cursor()
            id = request.user.id
            cur.execute('SELECT budget FROM notification_user WHERE id='+id.__str__()+';')
            tmp = cur.fetchone()
            cur.close()
            conn.close()
            return tmp
        def setBudget(request,val):
            conn = psycopg2.connect('dbname=pardpush user=pardpushs')
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
        #budget = getBudget(request)
        if cost <= request.user.budget:
            sendLoop(lst,msg)
            setBudget(request,request.user.budget-cost)
            return (True,cost)
        else:
            return (False,cost)
        
    def schedule(self, request, queryset):
        rc = get_redis_connection('default')
        scheduler = Scheduler(connection=rc)
        def createQuery(lst):
            query = 'SELECT phone FROM usabletable WHERE (tagname='
            if len(lst)==1:
                query += '\'' + lst[0].__str__() + '\')'
            else:
                for i in range(0, len(lst)-1):
                    query += '\'' + lst[i].__str__()+'\' OR tagname='
                query += '\'' + lst[-1].__str__() + '\''
                query += ") AND (sms_unsub=FALSE) GROUP BY phone"
            return query
        def sendQuery(query):
            conn = psycopg2.connect("dbname=pardpush user=matthewstern")
            cur = conn.cursor()
            cur.execute("REFRESH MATERIALIZED VIEW usabletable;")
            conn.commit()
            cur.execute(query)
            lst = cur.fetchall()
            cur.close()
            conn.close()
            return lst
        lst = sendQuery(createQuery(list(queryset.cleaned_data['tag'])))
        cost = len(lst) * .00562
        if cost <= request.user.budget:
            date = queryset.cleaned_data['date']
            timeshift = int(queryset.cleaned_data['shift'])
            delta = int(queryset.cleaned_data['delta'])
            timeunit = int(queryset.cleaned_data['timeunit'])
            if timeunit == 1:
                if(timeshift == 1):
                    scheduled_time = date - timedelta(minutes=delta)
                else:
                    scheduled_time = date + timedelta(minutes=delta)
                if scheduled_time.replace(tzinfo=None) < datetime.now():
                    return (False,cost)
                scheduler.enqueue_at(scheduled_time,send_scheduled_blast,kwargs={'request':'request','queryset':'queryset'})
                return (True,cost)
            elif timeunit == 2:
                if(timeshift == 3):
                    scheduled_time = date - timedelta(hours=delta)
                else:
                    scheduled_time = date + timedelta(hours=delta)
                if (scheduled_time.replace(tzinfo=None)) < datetime.now():
                    return (False,cost)
                scheduler.enqueue_at(scheduled_time,send_scheduled_blast,kwargs={'request':'request','queryset':'queryset'})
                return (True,cost)
            else:
                if(timeshift == 1):
                    scheduled_time = date - timedelta(days=delta)
                else:
                    scheduled_time = date + timedelta(days=delta)
                if (scheduled_time.replace(tzinfo=None)) < datetime.now():
                    return (False,cost)
                scheduler.enqueue_at(scheduled_time,send_scheduled_blast,kwargs={'request':'request','queryset':'queryset'})
                return (True,cost)
        else:
            return (False,cost)

def send_scheduled_blast(self, request, queryset):
    zucc = send_sms(request,queryset)
    
    #send email to organizer and tell them result of blast
    if zucc[0]: #budget was good!
        send_notification(request,queryset)
        subject = 'Scheduled Blast: ' + queryset.cleaned_data['name']
        body = 'Hi, ' + request.user.first_name + '!\n\n' 'Your scheduled blast for ' + queryset.cleaned_data['name'] + ' has been sent. \n\n -PardPush'
        send_mail(subject,body,'PardPush <pardpushhost@gmail.com>',request.user.email,fail_silently=True)
    else:
        subject = 'Failed Scheduled Blast: ' + queryset.cleaned_data['name']
        body = 'Hi, ' + request.user.first_name + '!\n\n' 'Your scheduled blast for ' + queryset.cleaned_data['name'] + ' has not been sent. This is most likely due to insufficient funds in your account.  Please contact the PardPush program chair for more information.\n\n -PardPush'
        msg = (subject,body,'PardPush <pardpushhost@gmail.com>',recipient)
        send_mail(subject,body,'PardPush <pardpushhost@gmail.com>',request.user.email,fail_silently=True)
