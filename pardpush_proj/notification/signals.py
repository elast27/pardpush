from django_cas_ng.signals import cas_user_authenticated
from django.dispatch import receiver

@receiver(cas_user_authenticated)
def update_role(sender, user=None, attributes=None, **kwargs):
    if kwargs.get('created',True):
        role = attributes['eduPersonEntitlement'].split('/')[3]
        user.email = attributes['username']+'@lafayette.edu'
        if role == 'faculty':
            user.is_organizer = True
        else:
            user.is_student = True
        user.save()
