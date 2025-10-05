#!/usr/bin/env python3
"""
Download NASA TEMPO data using earthaccess.

This script will prompt for NASA Earthdata credentials on first run.
To create an account, visit: https://urs.earthdata.nasa.gov/
"""
import earthaccess
import sys


def download_tempo_data(
    product="TEMPO_NO2_L3",
    start_date="2024-09-01",
    end_date="2024-09-05",
    bbox=(-74.259, 40.477, -73.700, 40.917),  # NYC
    output_dir="data/raw/tempo",
    max_files=5
):
    """
    Download TEMPO data files.

    Args:
        product: TEMPO product short name (e.g., TEMPO_NO2_L3, TEMPO_O3TOT_L3)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        bbox: Bounding box (lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)
        output_dir: Directory to save files
        max_files: Maximum number of files to download
    """
    print(f"Logging into NASA Earthdata...")
    auth = earthaccess.login()

    if not auth:
        print("Login failed. Please check your credentials.")
        sys.exit(1)

    print(f"\nSearching for {product} data...")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Bounding box: {bbox}")

    results = earthaccess.search_data(
        short_name=product,
        cloud_hosted=True,
        temporal=(start_date, end_date),
        bounding_box=bbox,
        count=max_files
    )

    print(f"\nFound {len(results)} granule(s)")

    if len(results) == 0:
        print("No data found for the specified criteria.")
        return

    print(f"\nDownloading {len(results)} file(s) to {output_dir}...")
    files = earthaccess.download(results, output_dir)

    if files:
        print(f"\n✓ Successfully downloaded {len(files)} file(s):")
        for f in files:
            print(f"  - {f}")
    else:
        print("\n✗ Download failed. Please check your credentials and try again.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download NASA TEMPO data")
    parser.add_argument(
        "--product",
        default="TEMPO_NO2_L3",
        help="TEMPO product (default: TEMPO_NO2_L3)"
    )
    parser.add_argument(
        "--start",
        default="2024-09-01",
        help="Start date YYYY-MM-DD (default: 2024-09-01)"
    )
    parser.add_argument(
        "--end",
        default="2024-09-05",
        help="End date YYYY-MM-DD (default: 2024-09-05)"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=5,
        help="Maximum files to download (default: 5)"
    )

    args = parser.parse_args()

    download_tempo_data(
        product=args.product,
        start_date=args.start,
        end_date=args.end,
        max_files=args.max_files
    )
