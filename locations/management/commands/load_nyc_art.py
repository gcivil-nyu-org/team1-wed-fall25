import csv
import json
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from locations.models import Location, Tag


class Command(BaseCommand):
    help = 'Load NYC public art data from CSV or JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to CSV or JSON file')
        parser.add_argument('--format', type=str, default='csv', choices=['csv', 'json'],
                            help='File format (csv or json)')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')

    def handle(self, *args, **options):
        file_path = options['file_path']
        file_format = options['format']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))

        # Get or create default tag
        public_art_tag, _ = Tag.objects.get_or_create(name='Public Art', defaults={'category': 'Art Type'})

        if file_format == 'csv':
            locations_data = self.load_csv(file_path)
        else:
            locations_data = self.load_json(file_path)

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for data in locations_data:
            try:
                result = self.process_location(data, public_art_tag, dry_run)
                if result == 'created':
                    created_count += 1
                elif result == 'updated':
                    updated_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {data.get("name", "unknown")}: {e}'))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nComplete! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}'
        ))

    def load_csv(self, file_path):
        """Load data from CSV file"""
        self.stdout.write(f'Loading CSV from {file_path}...')
        locations = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                locations.append(row)
        
        self.stdout.write(f'Found {len(locations)} rows')
        return locations

    def load_json(self, file_path):
        """Load data from JSON file"""
        self.stdout.write(f'Loading JSON from {file_path}...')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            locations = data
        elif isinstance(data, dict) and 'data' in data:
            locations = data['data']
        else:
            raise ValueError('Unexpected JSON structure')
        
        self.stdout.write(f'Found {len(locations)} records')
        return locations

    def process_location(self, data, default_tag, dry_run=False):
        """Process and save/update a single location"""
        # Extract fields (adapt to your CSV/JSON structure)
        # Common NYC Open Data fields
        name = data.get('title') or data.get('name') or data.get('artwork_title', '').strip()
        if not name:
            return 'skipped'

        description = data.get('description') or data.get('artwork_description', '')
        address = data.get('address') or data.get('location', '')
        
        # Latitude/Longitude (handle various formats)
        try:
            lat = self.parse_coordinate(data.get('latitude') or data.get('lat') or data.get('y_coord'))
            lng = self.parse_coordinate(data.get('longitude') or data.get('lng') or data.get('x_coord'))
            
            if lat is None or lng is None:
                # Try parsing from location field if available
                if 'location' in data and isinstance(data['location'], dict):
                    lat = self.parse_coordinate(data['location'].get('latitude'))
                    lng = self.parse_coordinate(data['location'].get('longitude'))
            
            if lat is None or lng is None or lat == 0 or lng == 0:
                self.stdout.write(self.style.WARNING(f'Skipping {name} - missing coordinates'))
                return 'skipped'
        except (ValueError, InvalidOperation) as e:
            self.stdout.write(self.style.WARNING(f'Skipping {name} - invalid coordinates: {e}'))
            return 'skipped'

        # Source ID
        source_id = data.get('id') or data.get('object_id') or data.get('uid', '')

        if dry_run:
            self.stdout.write(f'Would create/update: {name} at ({lat}, {lng})')
            return 'created'

        # Upsert logic
        if source_id:
            location, created = Location.objects.update_or_create(
                source='seeded',
                source_id=str(source_id),
                defaults={
                    'name': name[:200],
                    'description': description[:1000] if description else '',
                    'address': address[:300] if address else '',
                    'latitude': lat,
                    'longitude': lng,
                    'city': 'New York',
                    'state': 'NY',
                    'country': 'USA',
                }
            )
        else:
            # No source ID - check for duplicates by name and location
            location, created = Location.objects.get_or_create(
                name=name[:200],
                latitude=lat,
                longitude=lng,
                defaults={
                    'description': description[:1000] if description else '',
                    'address': address[:300] if address else '',
                    'source': 'seeded',
                    'city': 'New York',
                    'state': 'NY',
                    'country': 'USA',
                }
            )

        # Add default tag
        location.tags.add(default_tag)

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created: {name}'))
            return 'created'
        else:
            self.stdout.write(f'Updated: {name}')
            return 'updated'

    def parse_coordinate(self, value):
        """Parse coordinate from various formats"""
        if value is None or value == '':
            return None
        
        try:
            # Handle string or numeric
            if isinstance(value, str):
                value = value.strip()
                if not value or value.lower() in ['null', 'none', 'n/a']:
                    return None
            
            coord = Decimal(str(value))
            
            # Sanity check
            if coord == 0:
                return None
            
            return coord
        except (ValueError, InvalidOperation, TypeError):
            return None

