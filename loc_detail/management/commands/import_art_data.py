import requests
import csv
from io import StringIO
from django.core.management.base import BaseCommand
from loc_detail.models import PublicArt


class Command(BaseCommand):
    help = "Import NYC Public Art data from NYC Open Data API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=1000,
            help="Number of records to import (default: 1000, use 0 for all)",
        )

    def clean_value(self, value):
        """Clean a value, removing NULL, empty strings, and whitespace"""
        if not value:
            return None
        cleaned = value.strip()
        if not cleaned or cleaned.upper() == "NULL":
            return None
        return cleaned

    def handle(self, *args, **options):
        limit = options["limit"]

        # NYC Open Data API endpoint for the Public Art dataset
        base_url = "https://data.cityofnewyork.us/resource/2pg3-gcaa.csv"

        params = {}
        if limit > 0:
            params["$limit"] = limit
        else:
            params["$limit"] = 50000  # Maximum safe limit

        self.stdout.write(self.style.WARNING("Fetching data from NYC Open Data..."))

        try:
            response = requests.get(base_url, params=params, timeout=60)
            response.raise_for_status()

            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)

            created_count = 0
            updated_count = 0
            error_count = 0
            skipped_count = 0

            for row in reader:
                try:
                    # Build artist name from first, middle, last (clean all NULL values)
                    first = self.clean_value(row.get("primary_artist_first", ""))
                    middle = self.clean_value(row.get("primary_artist_middle", ""))
                    last = self.clean_value(row.get("primary_artist_last", ""))

                    # Build name only from non-NULL parts
                    artist_parts = [p for p in [first, middle, last] if p]
                    artist_name = " ".join(artist_parts) if artist_parts else None

                    # Get title
                    title = self.clean_value(row.get("title", ""))

                    # Skip if no title and no artist
                    if not title and not artist_name:
                        skipped_count += 1
                        continue

                    # Build location description
                    location_parts = []
                    location_name = self.clean_value(row.get("location_name"))
                    address = self.clean_value(row.get("address"))

                    if location_name:
                        location_parts.append(location_name)
                    if address:
                        location_parts.append(address)
                    location = ", ".join(location_parts) if location_parts else None

                    # Build description from available fields
                    description_parts = []
                    artwork_type = self.clean_value(row.get("artwork_type1"))
                    subject = self.clean_value(row.get("subject_keyword"))
                    inscription = self.clean_value(row.get("inscription"))

                    if artwork_type:
                        description_parts.append(f"Type: {artwork_type}")
                    if subject:
                        description_parts.append(f"Subject: {subject}")
                    if inscription and len(inscription) < 500:
                        description_parts.append(f"Inscription: {inscription}")

                    description = (
                        " | ".join(description_parts) if description_parts else None
                    )

                    # Prepare data with all fields cleaned
                    data = {
                        "artist_name": artist_name,
                        "title": title or "Untitled",
                        "description": description,
                        "location": location,
                        "borough": self.clean_value(row.get("borough")),
                        "medium": self.clean_value(row.get("material")),
                        "dimensions": None,
                        "year_created": self.clean_value(row.get("date_created")),
                        "year_dedicated": self.clean_value(row.get("date_dedicated")),
                        "agency": self.clean_value(row.get("managing_city_agency")),
                        "community_board": None,
                    }

                    # Handle coordinates
                    lat_str = self.clean_value(row.get("latitude"))
                    lon_str = self.clean_value(row.get("longitude"))

                    if lat_str:
                        try:
                            lat = float(lat_str)
                            if -90 <= lat <= 90:
                                data["latitude"] = lat
                        except (ValueError, TypeError):
                            pass

                    if lon_str:
                        try:
                            lon = float(lon_str)
                            if -180 <= lon <= 180:
                                data["longitude"] = lon
                        except (ValueError, TypeError):
                            pass

                    # Create unique identifier
                    external_id_parts = []
                    if title:
                        external_id_parts.append(title[:30])
                    if artist_name:
                        external_id_parts.append(artist_name[:30])
                    if data["borough"]:
                        external_id_parts.append(data["borough"][:20])
                    if data["year_created"]:
                        external_id_parts.append(data["year_created"][:10])

                    external_id = (
                        "_".join(external_id_parts)
                        if external_id_parts
                        else f"art_{created_count + updated_count}"
                    )
                    data["external_id"] = external_id[:100]

                    # Create or update record
                    art, created = PublicArt.objects.update_or_create(
                        external_id=data["external_id"], defaults=data
                    )

                    if created:
                        created_count += 1
                        if created_count % 50 == 0:
                            self.stdout.write(f"  Processed {created_count} records...")
                    else:
                        updated_count += 1

                except Exception as e:
                    error_count += 1
                    if error_count < 5:
                        self.stdout.write(
                            self.style.ERROR(f"Error processing row: {str(e)}")
                        )

            # Print summary
            self.stdout.write(self.style.SUCCESS("\n✓ Import completed successfully!"))
            self.stdout.write(f"  Created: {created_count}")
            self.stdout.write(f"  Updated: {updated_count}")
            self.stdout.write(f"  Skipped: {skipped_count}")
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f"  Errors: {error_count}"))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch data: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
