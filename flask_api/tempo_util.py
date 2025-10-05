"""
Helper module for reading NASA TEMPO NetCDF files and extracting pollutant values.
"""
import os
import glob


def get_most_recent_tempo_file(data_dir="data/raw/tempo"):
    """
    Get the most recently modified NetCDF file from the TEMPO data directory.

    Args:
        data_dir: Path to directory containing TEMPO NetCDF files

    Returns:
        Path to most recent file, or None if no files found
    """
    pattern = os.path.join(data_dir, "*.nc")
    files = glob.glob(pattern)

    if not files:
        return None

    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def auto_detect_pollutant_variable(ds):
    """
    Auto-detect the main pollutant variable in the dataset.

    Looks for variables with 'no2', 'ozone', 'o3', 'hcho' in their names.
    Falls back to first float-like 2D or 3D variable.

    Args:
        ds: xarray Dataset

    Returns:
        tuple: (variable_name, variable_object) or (None, None) if not found
    """
    import numpy as np

    # Priority keywords to search for
    keywords = ['no2', 'ozone', 'o3', 'hcho', 'co', 'formaldehyde']

    # First pass: look for keyword matches
    for var_name in ds.data_vars:
        var_lower = var_name.lower()
        for keyword in keywords:
            if keyword in var_lower:
                var = ds[var_name]
                # Check if it's 2D or 3D with lat/lon dimensions
                if len(var.dims) >= 2:
                    return var_name, var

    # Second pass: find first float-like 2D/3D variable
    for var_name in ds.data_vars:
        var = ds[var_name]
        if len(var.dims) >= 2 and np.issubdtype(var.dtype, np.floating):
            return var_name, var

    return None, None


def normalize_longitude(lon):
    """
    Normalize longitude to -180 to 180 range.

    Args:
        lon: Longitude value (can be 0-360 or -180-180)

    Returns:
        Normalized longitude in -180 to 180 range
    """
    lon = float(lon)
    while lon > 180:
        lon -= 360
    while lon < -180:
        lon += 360
    return lon


def is_location_in_tempo_coverage(lat, lon):
    """
    Check if a location is within TEMPO's coverage area (North America).

    TEMPO coverage:
    - Latitude: 17° to 64° (roughly Mexico to Alaska)
    - Longitude: -140° to -50° (Pacific to Atlantic)

    Args:
        lat: Latitude
        lon: Longitude (normalized to -180 to 180)

    Returns:
        bool: True if location is within coverage, False otherwise
    """
    normalized_lon = normalize_longitude(lon)

    # TEMPO coverage bounds (North America)
    lat_min, lat_max = 17.0, 64.0
    lon_min, lon_max = -140.0, -50.0

    return (lat_min <= lat <= lat_max) and (lon_min <= normalized_lon <= lon_max)


def get_nearest_value(file_path, lat, lon):
    """
    Extract the nearest pollutant value from a TEMPO NetCDF file for given coordinates.

    Returns None if location is outside TEMPO coverage area (North America).

    Args:
        file_path: Path to TEMPO NetCDF file
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180 or 0 to 360)

    Returns:
        dict with keys:
            - filename: Name of the file
            - variable_name: Name of the pollutant variable
            - unit: Unit of measurement
            - query_lat: Query latitude
            - query_lon: Query longitude (normalized)
            - nearest_lat: Actual latitude of nearest grid point
            - nearest_lon: Actual longitude of nearest grid point
            - value: Pollutant value at nearest point
            - error: Error message if any
    """
    result = {
        'filename': os.path.basename(file_path),
        'query_lat': lat,
        'query_lon': normalize_longitude(lon),
        'error': None
    }

    # Check if location is within TEMPO coverage
    if not is_location_in_tempo_coverage(lat, lon):
        result['error'] = f'Location ({lat}, {normalize_longitude(lon)}) is outside TEMPO coverage area (North America: 17-64°N, 140-50°W)'
        result['value'] = None
        return result

    try:
        import xarray as xr
        import numpy as np

        # Open dataset with h5netcdf engine
        ds = xr.open_dataset(file_path, engine='h5netcdf')

        # Auto-detect pollutant variable
        var_name, var = auto_detect_pollutant_variable(ds)

        if var_name is None:
            result['error'] = 'Could not detect pollutant variable in dataset'
            return result

        result['variable_name'] = var_name

        # Get unit if available
        unit = var.attrs.get('units', var.attrs.get('unit', 'unknown'))
        result['unit'] = unit

        # Detect latitude and longitude dimension names
        lat_dims = [d for d in var.dims if 'lat' in d.lower()]
        lon_dims = [d for d in var.dims if 'lon' in d.lower()]

        if not lat_dims or not lon_dims:
            result['error'] = f'Could not find lat/lon dimensions in variable {var_name}'
            return result

        lat_dim = lat_dims[0]
        lon_dim = lon_dims[0]

        # Get lat/lon coordinate arrays
        lats = ds[lat_dim].values
        lons = ds[lon_dim].values

        # Handle longitude coordinate system (normalize if needed)
        # Check if longitudes are in 0-360 range
        if lons.max() > 180:
            # Convert query longitude to 0-360
            query_lon_normalized = result['query_lon']
            if query_lon_normalized < 0:
                query_lon_normalized += 360
        else:
            query_lon_normalized = result['query_lon']

        # Find nearest indices
        lat_idx = np.argmin(np.abs(lats - lat))
        lon_idx = np.argmin(np.abs(lons - query_lon_normalized))

        result['nearest_lat'] = float(lats[lat_idx])
        result['nearest_lon'] = float(normalize_longitude(lons[lon_idx]))

        # Extract value at nearest point
        # Handle different dimensionality
        if len(var.dims) == 2:
            value = var.isel({lat_dim: lat_idx, lon_dim: lon_idx}).values
        elif len(var.dims) == 3:
            # If 3D, take first time/level slice
            other_dim = [d for d in var.dims if d not in [lat_dim, lon_dim]][0]
            value = var.isel({other_dim: 0, lat_dim: lat_idx, lon_dim: lon_idx}).values
        else:
            value = var.isel({lat_dim: lat_idx, lon_dim: lon_idx}).values

        # Convert to Python float (handle NaN)
        value = float(value)
        result['value'] = value if not np.isnan(value) else None

        ds.close()

    except Exception as e:
        result['error'] = str(e)

    return result
