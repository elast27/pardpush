from django_cas_ng.signals import cas_user_authenticated
from django.dispatch import receiver

@receiver(cas_user_authenticated)
def update_role(sender, user=None, attributes=None, **kwargs):
    if kwargs.values()[0]:
        role = attributes['eduPersonEntitlement'].split('/')[3]
        if role == 'faculty':
            user.is_organizer = True
        else:
            user.is_student = True
        user.save()
