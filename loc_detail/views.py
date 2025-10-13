from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import PublicArt, ArtComment


@login_required
def index(request):
    """Homepage with search and filter options"""
    # Get filter parameters
    search_query = request.GET.get('search', '')
    borough_filter = request.GET.get('borough', '')
    
    # Base queryset
    art_list = PublicArt.objects.all()
    
    # Apply search filter
    if search_query:
        art_list = art_list.filter(
            Q(title__icontains=search_query) |
            Q(artist_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply borough filter
    if borough_filter:
        art_list = art_list.filter(borough=borough_filter)
    
    # Get unique boroughs for filter dropdown
    boroughs = PublicArt.objects.exclude(borough__isnull=True).exclude(borough='').values_list('borough', flat=True).distinct().order_by('borough')
    
    # Pagination
    paginator = Paginator(art_list, 20)  # Show 20 art pieces per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'boroughs': boroughs,
        'search_query': search_query,
        'borough_filter': borough_filter,
        'total_count': art_list.count(),
    }
    
    return render(request, 'loc_detail/art_list.html', context)


@login_required
def art_detail(request, art_id):
    """Detail page for a specific art piece"""
    art = get_object_or_404(PublicArt, id=art_id)
    
    # Handle comment submission
    if request.method == 'POST':
        comment_text = request.POST.get('comment', '').strip()
        if comment_text:
            ArtComment.objects.create(
                user=request.user,
                art=art,
                comment=comment_text
            )
            messages.success(request, 'Your comment has been added!')
            return redirect('loc_detail:art_detail', art_id=art_id)
        else:
            messages.error(request, 'Comment cannot be empty.')
    
    # Get all comments for this art piece
    comments = art.comments.all()
    
    # Get related art pieces (same borough or same artist)
    related_art = PublicArt.objects.filter(
        Q(borough=art.borough) | Q(artist_name=art.artist_name)
    ).exclude(id=art.id)[:4]
    
    context = {
        'art': art,
        'comments': comments,
        'related_art': related_art,
    }
    
    return render(request, 'loc_detail/art_detail.html', context)