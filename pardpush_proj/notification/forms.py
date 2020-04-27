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
        student.phone = self.cleaned_data["phone"]
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
