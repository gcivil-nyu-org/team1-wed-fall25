from django.shortcuts import render
from django.http import HttpResponse

def location_list(request):
    return HttpResponse("Locations list - coming soon")

def location_create(request):
    return HttpResponse("Create location - coming soon")

def location_detail(request, pk):
    return HttpResponse(f"Location {pk} detail - coming soon")

def location_edit(request, pk):
    return HttpResponse(f"Edit location {pk} - coming soon")

def location_favorite_toggle(request, pk):
    return HttpResponse(f"Toggle favorite {pk} - coming soon")

def favorites_list(request):
    return HttpResponse("Favorites list - coming soon")
