from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView

from ..decorators import student_required
from ..forms import StudentInterestsForm, StudentSignUpForm
from ..models import Event, Student, User

from django.http import HttpResponse

class StudentSignUpView(CreateView):
    model = User
    form_class = StudentSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        #user = form.save()
        user = self.request.user
        student = Student.objects.create(user=user)
        student.interests.add(*form.cleaned_data.get('interests'))
        student.phone=form.cleaned_data["phone"]
        student.save()
        #login(self.request, user)
        form.send_initSMS(self.request, form) #sends welcome sms to the user
        return redirect('students:event_list')


@method_decorator([login_required, student_required], name='dispatch')
class StudentInterestsView(UpdateView):
    model = Student
    form_class = StudentInterestsForm
    template_name = 'notification/students/interests_form.html'
    success_url = reverse_lazy('students:event_list')

    def get_object(self):
        return self.request.user.student

    def form_valid(self, form):
        messages.success(self.request, 'Interests updated with success!')
        return super().form_valid(form)


@method_decorator([login_required, student_required], name='dispatch')
class EventListView(ListView):
    model = Event
    ordering = ('name', )
    context_object_name = 'events'
    template_name = 'notification/students/event_list.html'

    def get_queryset(self):
        queryset = Event.objects.all()
        return queryset

