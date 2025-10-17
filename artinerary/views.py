from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def index(request):
    return HttpResponse("Hello, world. You're at the Artinerary index.")
@login_required
def index(request):
    """Artinerary homepage with interactive map"""
    return render(request, 'artinerary/home.html')
