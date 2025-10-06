from django.http import HttpResponse

def itinerary_list(request):
    return HttpResponse("Itineraries list - coming soon")

def itinerary_create(request):
    return HttpResponse("Create itinerary - coming soon")

def itinerary_detail(request, pk):
    return HttpResponse(f"Itinerary {pk} detail - coming soon")

def itinerary_edit(request, pk):
    return HttpResponse(f"Edit itinerary {pk} - coming soon")

def itinerary_delete(request, pk):
    return HttpResponse(f"Delete itinerary {pk} - coming soon")

def itinerary_item_add(request, pk):
    return HttpResponse(f"Add item to itinerary {pk} - coming soon")

def itinerary_item_reorder(request, pk):
    return HttpResponse(f"Reorder items in itinerary {pk} - coming soon")

def itinerary_item_delete(request, itinerary_pk, item_pk):
    return HttpResponse(f"Delete item {item_pk} from itinerary {itinerary_pk} - coming soon")
