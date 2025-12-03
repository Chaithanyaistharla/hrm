from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import EmployeeProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_employee_profile(sender, instance, created, **kwargs):
    """
    Automatically create an EmployeeProfile when a new User is created.
    """
    if created:
        EmployeeProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_employee_profile(sender, instance, **kwargs):
    """
    Save the EmployeeProfile when the User is saved.
    """
    if hasattr(instance, 'employeeprofile'):
        instance.employeeprofile.save()
    else:
        # Create profile if it doesn't exist
        EmployeeProfile.objects.create(user=instance)