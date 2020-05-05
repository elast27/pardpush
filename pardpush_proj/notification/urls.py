from django.urls import include, path
from django.conf.urls import url
from .views import notification, students, organizers

urlpatterns = [
    path('', notification.home, name='home'),

    path('students/', include(([
        path('', students.EventListView.as_view(), name='event_list'),
        path('interests/', students.StudentInterestsView.as_view(), name='student_interests'),
    ], 'notification'), namespace='students')),

    path('organizers/', include(([
        path('', organizers.EventListView.as_view(), name='event_change_list'),
        path('event/add/', organizers.EventCreateView.as_view(), name='event_add'),
        path('event/<int:pk>/', organizers.EventUpdateView.as_view(), name='event_change'),
        path('event/<int:pk>/delete/', organizers.EventDeleteView.as_view(), name='event_delete'),
    ], 'notification'), namespace='organizers')),

    url(r'^ajax/get_cost/$', notification.get_cost, name='get_cost'),
]
