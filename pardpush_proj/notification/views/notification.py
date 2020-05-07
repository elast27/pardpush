from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.http import HttpResponse
from ..models import StudentsPerTag
import psycopg2
from datetime import datetime, timedelta
from django.utils import timezone

now = timezone.now()
class SignUpView(TemplateView):
    template_name = 'registration/signup.html'

def home(request):
    check_username(request)
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin/')
        elif request.user.is_organizer:
            return redirect('organizers:event_change_list')
        else:
            return redirect('students:event_list')
    return render(request, 'notification/home.html')

def check_username(request):
    if (request.user.date_joined).replace(tzinfo=None) + timedelta(minutes=1) - timedelta(hours=4) > datetime.now(): 
        return redirect('signup/student/')
    pass

def get_cost(request):
    def createQuery(lst):
        query = 'SELECT COUNT(student_id) FROM studentspertag WHERE (taglist LIKE ' 
        if len(lst)==1:
            query += '\'%' + lst[0] + '%\''
        else:
            for i in range(0,len(lst)-1):
                query += '\'%' + lst[i] + '%\' OR taglist LIKE '
            query += '\'%' + lst[-1].__str__() + '%\''
        query += ");"
        return query
    if request.method == 'POST':
        tagnames = request.POST.getlist('tags[]', None)
        if len(tagnames) == 0:
            return JsonResponse({ 
                'cost': 0
            })
        cst = 0
        conn = psycopg2.connect('dbname=pardpush user=matthewstern')
        cur = conn.cursor()
        cur.execute('REFRESH MATERIALIZED VIEW studentspertag;')
        conn.commit()
        cur.execute(createQuery(tagnames))
        tmp = cur.fetchone()
        cur.close()
        conn.close()
        cst = tmp[0] * .00562
        data = {
            'cost': cst
        }
        return JsonResponse(data)
    else:
        return HttpResponse("Request method is not a POST")
