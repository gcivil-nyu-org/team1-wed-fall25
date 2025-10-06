from django.http import HttpResponse

def event_list(request):
    return HttpResponse("Events list - coming soon")

def event_create(request):
    return HttpResponse("Create event - coming soon")

def event_detail(request, pk):
    return HttpResponse(f"Event {pk} detail - coming soon")

def event_edit(request, pk):
    return HttpResponse(f"Edit event {pk} - coming soon")

def event_delete(request, pk):
    return HttpResponse(f"Delete event {pk} - coming soon")

def event_invite(request, pk):
    return HttpResponse(f"Invite to event {pk} - coming soon")

def event_rsvp(request, pk):
    return HttpResponse(f"RSVP to event {pk} - coming soon")

def invite_accept(request, token):
    return HttpResponse(f"Accept invite {token} - coming soon")
