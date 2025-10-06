from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from .models import Report
from .forms import ReportForm


@login_required
def report_create(request):
    """Create a report for any content"""
    # Get content type and ID from query params
    content_type_name = request.GET.get('type', '')
    object_id = request.GET.get('id', '')
    
    if not content_type_name or not object_id:
        messages.error(request, 'Invalid report target.')
        return redirect('home')
    
    # Map friendly names to app labels
    type_map = {
        'location': ('locations', 'location'),
        'review': ('reviews', 'review'),
        'event': ('events', 'event'),
        'user': ('accounts', 'userprofile'),
    }
    
    if content_type_name not in type_map:
        messages.error(request, 'Invalid content type.')
        return redirect('home')
    
    app_label, model = type_map[content_type_name]
    
    try:
        content_type = ContentType.objects.get(app_label=app_label, model=model)
        content_object = content_type.get_object_for_this_type(pk=object_id)
    except Exception as e:
        messages.error(request, 'Content not found.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.content_type = content_type
            report.object_id = object_id
            report.save()
            messages.success(request, 'Report submitted. Our team will review it shortly.')
            
            # Redirect back to the content
            if hasattr(content_object, 'get_absolute_url'):
                return redirect(content_object.get_absolute_url())
            else:
                return redirect('home')
    else:
        form = ReportForm()
    
    context = {
        'form': form,
        'content_object': content_object,
        'content_type_name': content_type_name,
    }
    
    return render(request, 'reports/form.html', context)
