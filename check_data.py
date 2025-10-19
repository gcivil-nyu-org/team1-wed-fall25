import requests
import csv
from io import StringIO

print("Fetching data from NYC Open Data API...")

url = "https://data.cityofnewyork.us/resource/2pg3-gcaa.csv?$limit=3"

try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    csv_data = StringIO(response.text)
    reader = csv.DictReader(csv_data)

    # Get first row
    first_row = next(reader, None)

    if not first_row:
        print("No data returned!")
    else:
        print("\n" + "=" * 60)
        print("AVAILABLE CSV COLUMNS:")
        print("=" * 60)
        for i, col in enumerate(first_row.keys(), 1):
            print(f"{i:2d}. {col}")

        print("\n" + "=" * 60)
        print("SAMPLE DATA FROM FIRST ROW:")
        print("=" * 60)
        for key, value in first_row.items():
            if value and value.strip():
                display_value = value[:80] + "..." if len(value) > 80 else value
                print(f"\n{key}:")
                print(f"  {display_value}")

        print("\n" + "=" * 60)
        print("SUCCESS! Column names retrieved.")
        print("=" * 60)

except Exception as e:
    print(f"\nError: {e}")
    print("\nTrying alternative approach - downloading sample manually...")
    print(
        "Please visit: https://data.cityofnewyork.us/Housing-Development/Public-Design-Commission-Outdoor-Public-Art-Invent/2pg3-gcaa"  # noqa: E501
    )
    print("Click 'Export' and download CSV to see column names")
