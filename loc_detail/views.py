from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import PublicArt, ArtComment, UserFavoriteArt, CommentLike


@login_required
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

    # Get user's favorite art IDs
    user_favorites = list(
        UserFavoriteArt.objects.filter(user=request.user).values_list(
            "art_id", flat=True
        )
    )

    context = {
        "page_obj": page_obj,
        "boroughs": boroughs,
        "search_query": search_query,
        "borough_filter": borough_filter,
        "total_count": art_list.count(),
        "user_favorites": user_favorites,
    }

    return render(request, "loc_detail/art_list.html", context)


@login_required
def art_detail(request, art_id):
    """Detail page for a specific art piece"""
    art = get_object_or_404(PublicArt, id=art_id)

    # Handle comment/review submission
    if request.method == "POST":
        comment_text = request.POST.get("comment", "").strip()
        rating = request.POST.get("rating")
        parent_id = request.POST.get("parent_id")
        comment_id = request.POST.get("comment_id")  # For editing
        image = request.FILES.get("image")  # Get uploaded image

        if comment_text:
            parent_comment = None
            if parent_id:
                parent_comment = ArtComment.objects.filter(id=parent_id).first()

            # Check if editing existing comment
            if comment_id:
                try:
                    existing_comment = ArtComment.objects.get(
                        id=comment_id, user=request.user
                    )
                    existing_comment.comment = comment_text
                    if rating and not parent_comment:
                        existing_comment.rating = int(rating)
                    if image:
                        existing_comment.image = image
                    existing_comment.save()
                    messages.success(request, "Your review has been updated!")
                except ArtComment.DoesNotExist:
                    messages.error(
                        request,
                        "Comment not found or you don't have permission to edit it.",
                    )
            else:
                # Create new comment with rating (replies don't need rating)
                ArtComment.objects.create(
                    user=request.user,
                    art=art,
                    comment=comment_text,
                    rating=int(rating) if rating and not parent_comment else 5,
                    parent=parent_comment,
                    image=(
                        image if not parent_comment else None
                    ),  # Only main reviews can have images
                )

                if parent_comment:
                    messages.success(request, "Your reply has been added!")
                else:
                    messages.success(request, "Your review has been added!")

            return redirect("loc_detail:art_detail", art_id=art_id)
        else:
            messages.error(request, "Comment cannot be empty.")

    # Get top-level comments only (not replies)
    comments = art.comments.filter(parent__isnull=True).prefetch_related(
        "replies", "user"
    )

    # Add user reaction to each comment and reply
    for comment in comments:
        comment.user_reaction_status = comment.user_reaction(request.user)
        for reply in comment.replies.all():
            reply.user_reaction_status = reply.user_reaction(request.user)

    # Get user's existing review if any
    user_review = art.comments.filter(user=request.user, parent__isnull=True).first()

    # Get related art pieces (same borough or same artist)
    related_art = PublicArt.objects.filter(
        Q(borough=art.borough) | Q(artist_name=art.artist_name)
    ).exclude(id=art.id)[:4]

    # Check if user has favorited this art
    is_favorited = UserFavoriteArt.objects.filter(user=request.user, art=art).exists()

    # Get rating statistics
    avg_rating = art.get_average_rating()
    total_reviews = art.get_total_reviews()

    context = {
        "art": art,
        "comments": comments,
        "user_review": user_review,
        "related_art": related_art,
        "is_favorited": is_favorited,
        "avg_rating": avg_rating,
        "total_reviews": total_reviews,
    }

    return render(request, "loc_detail/art_detail.html", context)


@login_required
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
@require_POST
def api_comment_reaction(request, comment_id):
    """API endpoint to like/dislike a comment"""
    comment = get_object_or_404(ArtComment, id=comment_id)
    reaction_type = request.POST.get("reaction")  # 'like' or 'dislike'

    # Check if user already reacted
    existing_reaction = CommentLike.objects.filter(
        user=request.user, comment=comment
    ).first()

    if existing_reaction:
        # If same reaction, remove it (toggle off)
        if (existing_reaction.is_like and reaction_type == "like") or (
            not existing_reaction.is_like and reaction_type == "dislike"
        ):
            existing_reaction.delete()
            action = "removed"
        else:
            # Change reaction
            existing_reaction.is_like = reaction_type == "like"
            existing_reaction.save()
            action = "changed"
    else:
        # Create new reaction
        CommentLike.objects.create(
            user=request.user, comment=comment, is_like=(reaction_type == "like")
        )
        action = "added"

    # Refresh counts from database
    likes_count = comment.likes.filter(is_like=True).count()
    dislikes_count = comment.likes.filter(is_like=False).count()

    return JsonResponse(
        {
            "success": True,
            "action": action,
            "likes": likes_count,
            "dislikes": dislikes_count,
        }
    )


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
