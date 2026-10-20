
from django.shortcuts import render
from .models import Complejo


def inicio(request):
    complejos = Complejo.objects.all().prefetch_related("canchas")

    return render(
        request,
        "reservas/inicio.html",
        {"complejos": complejos},
    )
