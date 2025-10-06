from django.http import HttpResponse

def review_edit(request, pk):
    return HttpResponse(f"Edit review {pk} - coming soon")

def review_delete(request, pk):
    return HttpResponse(f"Delete review {pk} - coming soon")
