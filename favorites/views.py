"""
Views for unified favorites page
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q


@login_required
def favorites_view(request):
    """Unified favorites view with tabs for art, events, and itineraries"""
    from loc_detail.models import UserFavoriteArt
    from events.models import EventFavorite
    from itineraries.models import ItineraryFavorite

    # Get active tab from query parameter (default: art)
    active_tab = request.GET.get("tab", "art")

    # Initialize context
    context = {
        "active_tab": active_tab,
    }

    # Art Favorites
    if active_tab == "art":
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

        # Get unique boroughs for filter dropdown
        boroughs = (
            UserFavoriteArt.objects.filter(user=request.user)
            .values_list("art__borough", flat=True)
            .exclude(art__borough__isnull=True)
            .exclude(art__borough="")
            .distinct()
            .order_by("art__borough")
        )

        # Pagination
        paginator = Paginator(favorite_art, 20)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context.update(
            {
                "page_obj": page_obj,
                "boroughs": boroughs,
                "search_query": search_query,
                "borough_filter": borough_filter,
            }
        )

    # Events Favorites
    elif active_tab == "events":
        favorites_qs = (
            EventFavorite.objects.filter(user=request.user, event__is_deleted=False)
            .select_related("event", "event__host", "event__start_location")
            .order_by("-created_at")
        )

        # Add 'joined' attribute to each event
        from events.selectors import user_has_joined

        favorites_list = []
        for fav in favorites_qs:
            fav.event.joined = user_has_joined(fav.event, request.user)
            fav.event.favorited_at = fav.created_at
            favorites_list.append(fav.event)

        # Pagination
        paginator = Paginator(favorites_list, 12)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj

    # Itineraries Favorites
    elif active_tab == "itineraries":
        favorites_qs = (
            ItineraryFavorite.objects.filter(user=request.user)
            .select_related("itinerary", "itinerary__user")
            .prefetch_related("itinerary__stops", "itinerary__stops__location")
            .order_by("-created_at")
        )

        # Extract itineraries with favorited_at timestamp
        favorites_list = []
        for fav in favorites_qs:
            fav.itinerary.favorited_at = fav.created_at
            favorites_list.append(fav.itinerary)

        context["itineraries"] = favorites_list

    return render(request, "favorites/index.html", context)
