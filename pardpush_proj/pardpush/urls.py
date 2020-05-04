from django.urls import include, path
from django.contrib import admin
from notification.views import notification, students, organizers
import django_cas_ng.views

urlpatterns = [
    path('', include('notification.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', notification.SignUpView.as_view(), name='signup'),
    path('accounts/signup/student/', students.StudentSignUpView.as_view(), name='student_signup'),
    path('accounts/signup/organizer/', organizers.OrganizerSignUpView.as_view(), name='organizer_signup'),
    path('accounts/caslogin', django_cas_ng.views.LoginView.as_view(), name='cas_ng_login'),
    path('accounts/caslogout', django_cas_ng.views.LogoutView.as_view(), name='cas_ng_logout'),
]
