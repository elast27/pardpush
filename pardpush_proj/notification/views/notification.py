from django.shortcuts import redirect, render
from django.views.generic import TemplateView


class SignUpView(TemplateView):
    template_name = 'registration/signup.html'

def home(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return render(request, 'admin/base_site.html')
        elif request.user.is_organizer:
            return redirect('organizers:event_change_list')
        else:
            return redirect('students:event_list')
    return render(request, 'notification/home.html')
