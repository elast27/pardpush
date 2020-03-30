from django.urls import include, path

from notification.views import notification, students, organizers

urlpatterns = [
    path('', include('notification.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', notification.SignUpView.as_view(), name='signup'),
    path('accounts/signup/student/', students.StudentSignUpView.as_view(), name='student_signup'),
    path('accounts/signup/organizer/', organizers.OrganizerSignUpView.as_view(), name='organizer_signup'),
]
