from django.shortcuts import render


def homepage(request):
    """Homepage with map of nearby art locations"""
    return render(request, 'home.html')

