from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import PublicArt, ArtComment, UserFavoriteArt


# @login_required
def index(request):
    """Homepage with search and filter options"""
    # Get filter parameters
    search_query = request.GET.get("search", "")
    borough_filter = request.GET.get("borough", "")

    # Base queryset
    art_list = PublicArt.objects.all()

    # Apply search filter
    if search_query:
        art_list = art_list.filter(
            Q(title__icontains=search_query)
            | Q(artist_name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(location__icontains=search_query)
        )

    # Apply borough filter
    if borough_filter:
        art_list = art_list.filter(borough=borough_filter)

    # Get unique boroughs for filter dropdown
    boroughs = (
        PublicArt.objects.exclude(borough__isnull=True)
        .exclude(borough="")
        .values_list("borough", flat=True)
        .distinct()
        .order_by("borough")
    )

    # Pagination
    paginator = Paginator(art_list, 20)  # Show 20 art pieces per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "boroughs": boroughs,
        "search_query": search_query,
        "borough_filter": borough_filter,
        "total_count": art_list.count(),
    }

    return render(request, "loc_detail/art_list.html", context)


@login_required
def art_detail(request, art_id):
    """Detail page for a specific art piece"""
    art = get_object_or_404(PublicArt, id=art_id)

    # Handle comment submission
    if request.method == "POST":
        comment_text = request.POST.get("comment", "").strip()
        if comment_text:
            ArtComment.objects.create(user=request.user, art=art, comment=comment_text)
            messages.success(request, "Your comment has been added!")
            return redirect("loc_detail:art_detail", art_id=art_id)
        else:
            messages.error(request, "Comment cannot be empty.")

    # Get all comments for this art piece
    comments = art.comments.all()

    # Get related art pieces (same borough or same artist)
    related_art = PublicArt.objects.filter(
        Q(borough=art.borough) | Q(artist_name=art.artist_name)
    ).exclude(id=art.id)[:4]

    # Check if user has favorited this art
    is_favorited = UserFavoriteArt.objects.filter(user=request.user, art=art).exists()

    context = {
        "art": art,
        "comments": comments,
        "related_art": related_art,
        "is_favorited": is_favorited,
    }

    return render(request, "loc_detail/art_detail.html", context)


# @login_required
def api_all_points(request):
    """API endpoint returning all public art points as compact JSON"""
    # Fetch all art with valid coordinates
    art_points = PublicArt.objects.filter(
        latitude__isnull=False, longitude__isnull=False
    ).values("id", "title", "artist_name", "borough", "latitude", "longitude")[:5000]

    # Compact format: {id, t(itle), a(rtist), b(orough), y(lat), x(lng)}
    points = [
        {
            "id": art["id"],
            "t": art["title"] or "Untitled",
            "a": art["artist_name"] or "Unknown",
            "b": art["borough"] or "",
            "y": float(art["latitude"]),
            "x": float(art["longitude"]),
        }
        for art in art_points
    ]

    return JsonResponse({"points": points})


@login_required
@require_POST
def api_favorite_toggle(request, art_id):
    """API endpoint to toggle favorite status for an art piece"""
    art = get_object_or_404(PublicArt, id=art_id)

    # Check if already favorited
    favorite = UserFavoriteArt.objects.filter(user=request.user, art=art).first()

    if favorite:
        # Remove from favorites
        favorite.delete()
        favorited = False
        message = "Removed from favorites"
    else:
        # Add to favorites
        UserFavoriteArt.objects.create(user=request.user, art=art)
        favorited = True
        message = "Added to favorites"

    return JsonResponse({"favorited": favorited, "message": message})


@login_required
def favorites(request):
    """Display user's favorite art pieces"""
    # Get user's favorite art pieces
    favorite_art = (
        UserFavoriteArt.objects.filter(user=request.user)
        .select_related("art")
        .order_by("-added_at")
    )

    # Get filter parameters
    search_query = request.GET.get("search", "")
    borough_filter = request.GET.get("borough", "")

    # Apply search filter
    if search_query:
        favorite_art = favorite_art.filter(
            Q(art__title__icontains=search_query)
            | Q(art__artist_name__icontains=search_query)
            | Q(art__description__icontains=search_query)
            | Q(art__location__icontains=search_query)
        )

    # Apply borough filter
    if borough_filter:
        favorite_art = favorite_art.filter(art__borough=borough_filter)

    # Get unique boroughs for filter dropdown (from user's favorites only)
    boroughs = (
        favorite_art.values_list("art__borough", flat=True)
        .exclude(art__borough__isnull=True)
        .exclude(art__borough="")
        .distinct()
        .order_by("art__borough")
    )

    # Pagination
    paginator = Paginator(favorite_art, 20)  # Show 20 favorites per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "boroughs": boroughs,
        "search_query": search_query,
        "borough_filter": borough_filter,
        "total_count": favorite_art.count(),
    }

    return render(request, "loc_detail/favorites.html", context)
