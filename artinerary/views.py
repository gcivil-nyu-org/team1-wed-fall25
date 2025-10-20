from django.shortcuts import render

# from django.contrib.auth.decorators import login_required


# @login_required
def index(request):
    """Artinerary homepage with interactive map"""
    return render(request, "artinerary/home.html")
