from django.conf import settings
from django.utils import timezone


def globals(request):
    return {
        "APP_NAME": getattr(settings, "APP_NAME", "Biblioteca"),
        "hoy": timezone.localdate(),
    }
