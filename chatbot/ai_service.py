import google.generativeai as genai
from django.conf import settings
from django.utils import timezone
from loc_detail.models import PublicArt
from django.db.models import Q
import re
import pytz
import math


class ArtineraryAI:
    def __init__(self):
        # Initialize Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-pro")
        self.est_tz = pytz.timezone("America/New_York")

    def get_current_time_est(self):
        """Get current time in EST format"""
        now_est = timezone.now().astimezone(self.est_tz)
        return now_est.strftime("%m/%d/%Y %I:%M %p EST")

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in miles"""
        R = 3959  # Earth's radius in miles

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def get_nearby_artworks(self, user_lat, user_lon, limit=5, radius_miles=2):
        """Get artworks near user's location"""
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
        except (ValueError, TypeError) as e:
            print(f"Invalid coordinates: lat={user_lat}, " f"lon={user_lon}, error={e}")
            return []

        artworks = PublicArt.objects.filter(
            latitude__isnull=False, longitude__isnull=False
        )

        print(f"Total artworks in database: {artworks.count()}")
        print(f"User location: lat={user_lat}, lon={user_lon}")

        nearby = []
        for art in artworks:
            try:
                distance = self.calculate_distance(
                    user_lat,
                    user_lon,
                    float(art.latitude),
                    float(art.longitude),
                )
                if distance <= radius_miles:
                    nearby.append(
                        {
                            "id": art.id,
                            "title": art.title or "Untitled",
                            "artist": art.artist_name or "Unknown",
                            "location": (art.location or "Location not specified"),
                            "borough": art.borough or "",
                            "distance": round(distance, 2),
                        }
                    )
            except Exception as e:
                print(f"Error calculating distance for artwork {art.id}: {e}")
                continue

        # Sort by distance and return top results
        nearby.sort(key=lambda x: x["distance"])
        print(f"Found {len(nearby)} artworks within {radius_miles} miles")
        return nearby[:limit]

    def search_artworks(self, query):
        """Search artworks by various criteria"""
        artworks = PublicArt.objects.filter(
            Q(title__icontains=query)
            | Q(artist_name__icontains=query)
            | Q(location__icontains=query)
            | Q(borough__icontains=query)
            | Q(medium__icontains=query)
        )[:10]

        return [
            {
                "id": art.id,
                "title": art.title or "Untitled",
                "artist": art.artist_name or "Unknown",
                "location": art.location or "Location not specified",
                "borough": art.borough or "",
                "medium": art.medium or "",
            }
            for art in artworks
        ]

    def plan_itinerary(self, preferences, user_location=None):
        """Plan an itinerary based on user preferences"""
        borough = preferences.get("borough", "")
        theme = preferences.get("theme", "")
        duration = preferences.get("duration", 3)  # hours

        # Start with all artworks
        query = PublicArt.objects.filter(
            latitude__isnull=False, longitude__isnull=False
        )

        # Filter by borough if specified
        if borough:
            query = query.filter(borough__icontains=borough)

        # Filter by theme/medium if specified
        if theme:
            query = query.filter(
                Q(medium__icontains=theme)
                | Q(title__icontains=theme)
                | Q(description__icontains=theme)
            )

        # Get artworks
        artworks = query[: duration * 2]

        itinerary_items = []
        for i, art in enumerate(artworks):
            itinerary_items.append(
                {
                    "id": art.id,
                    "order": i + 1,
                    "title": art.title or "Untitled",
                    "artist": art.artist_name or "Unknown",
                    "location": art.location or "Location not specified",
                    "borough": art.borough or "",
                    "estimated_time": f"{30 * (i + 1)} minutes",
                }
            )

        return itinerary_items

    def get_navigation_help(self, page_request):
        """Provide navigation assistance"""
        navigation_map = {
            "map": {"url": "/artinerary/", "name": "Interactive Map"},
            "artworks": {"url": "/loc_detail/", "name": "Browse Artworks"},
            "artwork": {"url": "/loc_detail/", "name": "Browse Artworks"},
            "events": {"url": "/events/", "name": "Events"},
            "event": {"url": "/events/", "name": "Events"},
            "itinerary": {
                "url": "/itineraries/",
                "name": "My Itineraries",
            },
            "itineraries": {
                "url": "/itineraries/",
                "name": "My Itineraries",
            },
            "profile": {"url": "/profile/", "name": "My Profile"},
            "favorites": {"url": "/favorites/", "name": "My Favorites"},
            "favorite": {"url": "/favorites/", "name": "My Favorites"},
        }

        for key, value in navigation_map.items():
            if key in page_request.lower():
                return value

        return None

    def get_help_response(self, query):
        """Provide help responses for common queries"""
        help_topics = {
            "edit profile": {
                "response": (
                    "To edit your profile:\n"
                    "1. Click on your profile avatar in the top right\n"
                    '2. Select "Edit Profile" from the dropdown\n'
                    "3. Update your information\n"
                    '4. Click "Save Changes"'
                ),
                "button": {
                    "text": "Edit Profile",
                    "url": "/user_profile/edit/",
                },
            },
            "create itinerary": {
                "response": (
                    "To create an itinerary:\n"
                    '1. Go to "My Itineraries" from the navigation\n'
                    '2. Click "Create New Itinerary"\n'
                    "3. Add locations and set your route\n"
                    "4. Save your itinerary"
                ),
                "button": {
                    "text": "Create Itinerary",
                    "url": "/itineraries/create/",
                },
            },
            "add favorite": {
                "response": (
                    "To add an artwork to favorites:\n"
                    "1. Browse or search for artworks\n"
                    "2. Click on an artwork to view details\n"
                    "3. Click the heart icon to add to favorites"
                ),
                "button": {
                    "text": "Browse Artworks",
                    "url": "/loc_detail/",
                },
            },
            "create event": {
                "response": (
                    "To create an event:\n"
                    '1. Go to "Events" from the navigation\n'
                    '2. Click "Create Event"\n'
                    "3. Fill in event details\n"
                    "4. Publish your event"
                ),
                "button": {
                    "text": "Create Event",
                    "url": "/events/create/",
                },
            },
        }

        query_lower = query.lower()
        for topic, info in help_topics.items():
            if topic in query_lower:
                return info

        return None

    def process_message(self, message, user, user_location=None):
        """Main message processing function"""
        message_lower = message.lower()
        response_data = {"message": "", "metadata": {}}

        print(f"Processing message: {message}")
        print(f"User location received: {user_location}")

        # Check for artwork suggestions request
        if any(
            word in message_lower
            for word in [
                "nearby",
                "near me",
                "around me",
                "close by",
                "close to me",
            ]
        ):
            if user_location:
                # Handle both formats: {lat, lng} and {latitude, longitude}
                lat = user_location.get("lat") or user_location.get("latitude")
                lng = user_location.get("lng") or user_location.get("longitude")

                print(f"Extracted coordinates: lat={lat}, lng={lng}")

                if lat and lng:
                    nearby_art = self.get_nearby_artworks(lat, lng)
                    if nearby_art:
                        response_data["message"] = (
                            f"Here are {len(nearby_art)} artworks near "
                            f"you:\n\nWould you like to create an "
                            f"itinerary with these locations?"
                        )
                        response_data["metadata"]["artworks"] = nearby_art
                        response_data["metadata"]["show_itinerary_prompt"] = True
                        response_data["metadata"]["suggested_locations"] = [
                            art["id"] for art in nearby_art
                        ]
                    else:
                        response_data["message"] = (
                            "No artworks found within 2 miles of your "
                            "location. Try expanding the search radius or "
                            "exploring other areas!"
                        )
                else:
                    response_data["message"] = (
                        "I couldn't read your location coordinates. "
                        "Please share your location again."
                    )
                    response_data["metadata"]["request_location"] = True
            else:
                response_data["message"] = (
                    "Please share your location using the location "
                    "button to find nearby artworks."
                )
                response_data["metadata"]["request_location"] = True

        # Check for itinerary planning
        elif any(
            word in message_lower
            for word in [
                "plan",
                "itinerary",
                "route",
                "tour",
                "create itinerary",
            ]
        ):
            # Extract preferences from message
            preferences = {}

            # Check for borough
            boroughs = [
                "manhattan",
                "brooklyn",
                "queens",
                "bronx",
                "staten island",
            ]
            for borough in boroughs:
                if borough in message_lower:
                    preferences["borough"] = borough.title()
                    break

            # Check for duration
            duration_match = re.search(r"(\d+)\s*hour", message_lower)
            if duration_match:
                preferences["duration"] = int(duration_match.group(1))

            itinerary = self.plan_itinerary(preferences, user_location)
            if itinerary:
                response_data["message"] = (
                    f"I've planned an itinerary with {len(itinerary)} "
                    f"stops:\n\nWould you like to create an itinerary "
                    f"with these locations?"
                )
                response_data["metadata"]["itinerary"] = itinerary
                response_data["metadata"]["show_itinerary_prompt"] = True
                response_data["metadata"]["suggested_locations"] = [
                    stop["id"] for stop in itinerary
                ]
            else:
                response_data["message"] = (
                    "I couldn't find enough artworks for your criteria. "
                    "Try being less specific."
                )

        # Check for navigation help
        elif any(
            word in message_lower
            for word in ["go to", "navigate", "show me", "take me"]
        ):
            nav_info = self.get_navigation_help(message_lower)
            if nav_info:
                response_data["message"] = (
                    f"I'll help you navigate to {nav_info['name']}."
                )
                response_data["metadata"]["navigation"] = nav_info
            else:
                response_data["message"] = (
                    "I'm not sure which page you want to visit. Try: "
                    "map, artworks, events, itineraries, or profile."
                )

        # Check for help queries
        elif any(word in message_lower for word in ["help", "how to", "how do i"]):
            help_info = self.get_help_response(message_lower)
            if help_info:
                response_data["message"] = help_info["response"]
                if "button" in help_info:
                    response_data["metadata"]["action_button"] = help_info["button"]
            else:
                # Use Gemini for general help
                context = (
                    "You are an AI assistant for Artinerary, a NYC "
                    "public art exploration platform.\n"
                    f"Current time: {self.get_current_time_est()}\n"
                    f"User question: {message}\n\n"
                    "Provide helpful, concise guidance about using the "
                    "website features like browsing art, creating "
                    "itineraries, attending events, and managing profile."
                )

                try:
                    gemini_response = self.model.generate_content(context)
                    response_data["message"] = gemini_response.text
                except Exception as e:
                    print(f"Gemini API error: {e}")
                    response_data["message"] = (
                        "I'm here to help! You can ask me about finding "
                        "artworks, planning itineraries, or navigating "
                        "the site."
                    )

        # Search for specific artworks
        elif any(word in message_lower for word in ["find", "search", "show"]):
            # Extract search term
            search_terms = (
                message_lower.replace("find", "")
                .replace("search", "")
                .replace("show", "")
                .strip()
            )
            if search_terms:
                results = self.search_artworks(search_terms)
                if results:
                    response_data["message"] = (
                        f"I found {len(results)} artworks matching "
                        f"'{search_terms}':"
                    )
                    response_data["metadata"]["search_results"] = results
                else:
                    response_data["message"] = (
                        f"No artworks found matching '{search_terms}'. "
                        f"Try different keywords."
                    )
            else:
                response_data["message"] = (
                    "What would you like to search for? Try artist "
                    "names, artwork titles, or locations."
                )

        # Default: Use Gemini for general conversation
        else:
            context = (
                "You are ArtBot, an AI assistant for Artinerary, "
                "helping users explore NYC public art.\n"
                f"Current time: {self.get_current_time_est()}\n"
                f"User: {message}\n\n"
                "Respond helpfully and concisely. You can help with:\n"
                "- Finding artworks and planning art tours\n"
                "- Creating itineraries\n"
                "- Navigating the website\n"
                "- Understanding NYC public art\n\n"
                "Keep responses friendly and under 3 sentences "
                "when possible."
            )

            try:
                gemini_response = self.model.generate_content(context)
                response_data["message"] = gemini_response.text
            except Exception as e:
                print(f"Gemini API error: {e}")
                response_data["message"] = (
                    "I'm here to help you explore NYC public art! "
                    "Ask me about nearby artworks, planning itineraries, "
                    "or any questions about using Artinerary."
                )

        print(f"Response: {response_data['message']}")
        print(f"Metadata: {response_data['metadata']}")

        return response_data
