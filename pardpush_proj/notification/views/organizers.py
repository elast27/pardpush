from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from ..decorators import organizer_required
from ..forms import OrganizerSignUpForm, DateForm, TagSelectForm
from ..models import Event, User
from django import forms


class OrganizerSignUpView(CreateView):
    model = User
    form_class = OrganizerSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'organizer'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('organizers:event_change_list')


@method_decorator([login_required, organizer_required], name='dispatch')
class EventListView(ListView):
    model = Event
    ordering = ('name', )
    context_object_name = 'events'
    template_name = 'notification/organizers/event_change_list.html'

    def get_queryset(self):
        queryset = self.request.user.events.all()
        return queryset


@method_decorator([login_required, organizer_required], name='dispatch')
class EventCreateView(CreateView):
    form_class = TagSelectForm
    model = Event
    # fields = ('name', 'tag', 'date', 'location', 'message', )
    template_name = 'notification/organizers/event_add_form.html'

    def form_valid(self, form):
        event = form.save(commit=False)
        event.owner = self.request.user
        some_var = self.request.POST.getlist('tag') # Gives a list of tags chosen by the user 
        succ = form.send_SMS(self.request, form) #Send SMS notification
        if succ[0]:
            form.send_notification(self.request, form) # Send email notification
            event.save()
            for obj in some_var:
                event.tag.add(obj)
            messages.success(self.request, 'The event was created with success!')
            return redirect('home')
        else:
            messages.error(self.request, 'You do not have enough funds to complete this request. Cost: $' + succ[1].__str__() + '.  Please contact PardPush admin to add more funds.')
        return redirect('organizers:event_change', event.pk)


@method_decorator([login_required, organizer_required], name='dispatch')
class EventUpdateView(UpdateView):
    model = Event
    fields = ('name', 'tag', 'date', 'location', 'message', )
    context_object_name = 'event'
    template_name = 'notification/organizers/event_change_form.html'

    def get_queryset(self):
        '''
        This method is an implicit object-level permission management
        This view will only match the ids of existing events that belongs
        to the logged in user.
        '''
        return self.request.user.events.all()

    def get_success_url(self):
        return reverse('organizers:event_change', kwargs={'pk': self.object.pk})


@method_decorator([login_required, organizer_required], name='dispatch')
class EventDeleteView(DeleteView):
    model = Event
    context_object_name = 'event'
    template_name = 'notification/organizers/event_delete_confirm.html'
    success_url = reverse_lazy('organizers:event_change_list')

    def delete(self, request, *args, **kwargs):
        event = self.get_object()
        messages.success(request, 'The event %s was deleted with success!' % event.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.events.all()


@method_decorator([login_required, organizer_required], name='dispatch')
class EventResultsView(DetailView):
    model = Event
    context_object_name = 'event'
    template_name = 'notification/organizers/event_results.html'

    def get_context_data(self, **kwargs):
        event = self.get_object()
        taken_events = event.taken_events.select_related('student__user').order_by('-date')
        total_taken_events = taken_events.count()
        event_score = event.taken_events.aggregate(average_score=Avg('score'))
        extra_context = {
            'taken_qevents': taken_events,
            'total_taken_events': total_taken_events,
            'event_score': event_score
        }
        kwargs.update(extra_context)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.events.all()

