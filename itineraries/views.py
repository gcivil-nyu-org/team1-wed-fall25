"""
Views for the itineraries app
FIXED VERSION - Addresses all reported issues
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Itinerary, ItineraryStop
from .forms import ItineraryForm, ItineraryStopFormSet
from loc_detail.models import PublicArt


@login_required
def itinerary_list(request):
    """View for listing all user's itineraries"""
    from .models import ItineraryFavorite

    itineraries = Itinerary.objects.filter(user=request.user).prefetch_related(
        "stops", "stops__location"
    )

    # Get favorited itinerary IDs for this user
    favorited_ids = set(
        ItineraryFavorite.objects.filter(user=request.user).values_list(
            "itinerary_id", flat=True
        )
    )

    # Add is_favorited attribute to each itinerary
    for itinerary in itineraries:
        itinerary.is_favorited = itinerary.id in favorited_ids

    context = {
        "itineraries": itineraries,
        "is_favorites_view": False,
    }
    return render(request, "itineraries/list.html", context)


@login_required
def itinerary_detail(request, pk):
    """View for displaying a single itinerary"""
    from .models import ItineraryFavorite

    itinerary = get_object_or_404(
        Itinerary.objects.prefetch_related("stops", "stops__location"),
        pk=pk,
        user=request.user,
    )

    # Check if favorited
    is_favorited = ItineraryFavorite.objects.filter(
        itinerary=itinerary, user=request.user
    ).exists()

    context = {
        "itinerary": itinerary,
        "is_favorited": is_favorited,
    }
    return render(request, "itineraries/detail.html", context)


@login_required
def itinerary_create(request):
    """View for creating a new itinerary"""
    if request.method == "POST":
        form = ItineraryForm(request.POST)
        formset = ItineraryStopFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Save itinerary first
                    itinerary = form.save(commit=False)
                    itinerary.user = request.user
                    itinerary.save()

                    # Collect valid stops
                    stops_data = []
                    for form_instance in formset.forms:
                        if (
                            form_instance.cleaned_data
                            and not form_instance.cleaned_data.get("DELETE", False)
                        ):
                            location = form_instance.cleaned_data.get("location")
                            if location:
                                stops_data.append(
                                    {
                                        "location": location,
                                        "visit_time": form_instance.cleaned_data.get(
                                            "visit_time"
                                        ),
                                        "notes": form_instance.cleaned_data.get(
                                            "notes", ""
                                        ),
                                    }
                                )

                    # Create stops with sequential ordering
                    for i, stop_data in enumerate(stops_data):
                        ItineraryStop.objects.create(
                            itinerary=itinerary,
                            location=stop_data["location"],
                            order=i + 1,
                            visit_time=stop_data["visit_time"],
                            notes=stop_data["notes"],
                        )

                    messages.success(
                        request, f'Itinerary "{itinerary.title}" created successfully!'
                    )
                    return redirect("itineraries:detail", pk=itinerary.pk)
            except Exception as e:
                messages.error(request, f"Error creating itinerary: {str(e)}")
        else:
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
            if not formset.is_valid():
                for i, form_errors in enumerate(formset.errors):
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(request, f"Stop {i+1} - {field}: {error}")
    else:
        form = ItineraryForm()
        formset = ItineraryStopFormSet()

    # Get all locations for the dropdown
    locations = PublicArt.objects.filter(
        latitude__isnull=False, longitude__isnull=False
    ).order_by("title")

    context = {
        "form": form,
        "formset": formset,
        "locations": locations,
        "is_edit": False,
    }
    return render(request, "itineraries/create_improved.html", context)


@login_required
def itinerary_edit(request, pk):
    """View for editing an existing itinerary - FIXED VERSION"""
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)

    if request.method == "POST":
        form = ItineraryForm(request.POST, instance=itinerary)
        formset = ItineraryStopFormSet(request.POST, instance=itinerary)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Save the itinerary form
                    form.save()

                    # Collect new stops data
                    new_stops_data = []

                    for form_instance in formset.forms:
                        # Skip if marked for deletion
                        if form_instance.cleaned_data.get("DELETE", False):
                            continue

                        # Only process if has location
                        location = form_instance.cleaned_data.get("location")
                        if location:
                            new_stops_data.append(
                                {
                                    "location": location,
                                    "visit_time": form_instance.cleaned_data.get(
                                        "visit_time"
                                    ),
                                    "notes": form_instance.cleaned_data.get(
                                        "notes", ""
                                    ),
                                }
                            )

                    # Delete ALL existing stops
                    itinerary.stops.all().delete()

                    # Recreate stops with new sequential ordering
                    for i, stop_data in enumerate(new_stops_data):
                        ItineraryStop.objects.create(
                            itinerary=itinerary,
                            location=stop_data["location"],
                            order=i + 1,
                            visit_time=stop_data["visit_time"],
                            notes=stop_data["notes"],
                        )

                    messages.success(
                        request, f'Itinerary "{itinerary.title}" updated successfully!'
                    )
                    return redirect("itineraries:detail", pk=itinerary.pk)
            except Exception as e:
                messages.error(request, f"Error updating itinerary: {str(e)}")
        else:
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
            if not formset.is_valid():
                for i, form_errors in enumerate(formset.errors):
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(request, f"Stop {i+1} - {field}: {error}")
    else:
        form = ItineraryForm(instance=itinerary)
        formset = ItineraryStopFormSet(instance=itinerary)

    # Get all locations for the dropdown
    locations = PublicArt.objects.filter(
        latitude__isnull=False, longitude__isnull=False
    ).order_by("title")

    context = {
        "form": form,
        "formset": formset,
        "locations": locations,
        "itinerary": itinerary,
        "is_edit": True,
    }
    return render(request, "itineraries/create_improved.html", context)


@login_required
def itinerary_delete(request, pk):
    """View for deleting an itinerary"""
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)

    if request.method == "POST":
        title = itinerary.title
        itinerary.delete()
        messages.success(request, f'Itinerary "{title}" deleted successfully!')
        return redirect("itineraries:list")

    context = {
        "itinerary": itinerary,
    }
    return render(request, "itineraries/delete_confirm.html", context)


@login_required
def api_search_locations(request):
    """API endpoint for searching locations"""
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"results": []})

    locations = PublicArt.objects.filter(
        latitude__isnull=False, longitude__isnull=False
    ).filter(title__icontains=query)[:20]

    results = [
        {
            "id": loc.id,
            "title": loc.title or "Untitled",
            "artist": loc.artist_name or "Unknown",
            "borough": loc.borough or "",
            "location": loc.location or "",
        }
        for loc in locations
    ]

    return JsonResponse({"results": results})


@login_required
def api_get_user_itineraries(request):
    """API endpoint for getting user's itineraries"""
    itineraries = Itinerary.objects.filter(user=request.user).order_by("-created_at")

    results = [
        {
            "id": itin.id,
            "title": itin.title,
            "stop_count": itin.stops.count(),
        }
        for itin in itineraries
    ]

    return JsonResponse({"itineraries": results})


@login_required
@require_POST
def api_add_to_itinerary(request):
    """API endpoint for adding a location to an itinerary"""
    try:
        location_id = request.POST.get("location_id")
        itinerary_id = request.POST.get("itinerary_id")
        new_itinerary_title = request.POST.get("new_itinerary_title")

        # Validate location
        location = get_object_or_404(PublicArt, id=location_id)

        # Handle creating new itinerary or using existing one
        if new_itinerary_title:
            # Create new itinerary
            itinerary = Itinerary.objects.create(
                user=request.user, title=new_itinerary_title.strip()
            )
            order = 1
        elif itinerary_id:
            # Use existing itinerary
            itinerary = get_object_or_404(Itinerary, id=itinerary_id, user=request.user)
            # Get the next order number
            last_stop = itinerary.stops.order_by("-order").first()
            order = (last_stop.order + 1) if last_stop else 1
        else:
            return JsonResponse(
                {"success": False, "error": "No itinerary specified"}, status=400
            )

        # Check if location already exists in this itinerary
        if ItineraryStop.objects.filter(
            itinerary=itinerary, location=location
        ).exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": f"This location is already in {itinerary.title}",
                },
                status=400,
            )

        # Add the location to the itinerary
        ItineraryStop.objects.create(
            itinerary=itinerary, location=location, order=order
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Added to {itinerary.title}",
                "itinerary_id": itinerary.id,
                "itinerary_url": itinerary.get_absolute_url(),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def favorite_itinerary(request, pk):
    """Add itinerary to user's favorites"""
    from .models import ItineraryFavorite

    itinerary = get_object_or_404(Itinerary, pk=pk)

    try:
        # Create favorite (idempotent)
        ItineraryFavorite.objects.get_or_create(itinerary=itinerary, user=request.user)
        messages.success(request, f'Added "{itinerary.title}" to favorites.')
    except Exception as e:
        messages.error(request, f"Failed to add to favorites: {str(e)}")

    # Redirect back to the referring page or itinerary detail
    return redirect(request.META.get("HTTP_REFERER", itinerary.get_absolute_url()))


@login_required
@require_POST
def unfavorite_itinerary(request, pk):
    """Remove itinerary from user's favorites"""
    from .models import ItineraryFavorite

    itinerary = get_object_or_404(Itinerary, pk=pk)

    try:
        deleted_count, _ = ItineraryFavorite.objects.filter(
            itinerary=itinerary, user=request.user
        ).delete()

        if deleted_count > 0:
            messages.success(request, f'Removed "{itinerary.title}" from favorites.')
        else:
            messages.info(request, "This itinerary was not in your favorites.")
    except Exception as e:
        messages.error(request, f"Failed to remove from favorites: {str(e)}")

    # Redirect back to the referring page or itinerary detail
    return redirect(request.META.get("HTTP_REFERER", itinerary.get_absolute_url()))


@login_required
def favorites(request):
    """Display user's favorite itineraries"""
    from .models import ItineraryFavorite

    # Get favorited itineraries
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

    context = {
        "itineraries": favorites_list,
        "is_favorites_view": True,
    }

    return render(request, "itineraries/favorites.html", context)
