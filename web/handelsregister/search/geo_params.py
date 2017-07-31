from django.contrib.gis.geos import Point


def get_request_coord(query_params):
    """
    Retrieves the coordinates to work with. It allows for either lat/lon coord,
    for wgs84 or 'x' and 'y' for RD. Just to be on the safe side a value check
    a value check is done to make sure that the values are within the expected
    range.

    Parameters:
    query_params - the query parameters dict from which to retrieve the coords

    Returns coordinates in WSG84 longitude,latitude
    """
    if 'lat' in query_params and 'lon' in query_params:
        lon = float(query_params['lon'])
        lat = float(query_params['lat'])
        return _convert_coords(lon, lat, 4326, 28992)
    elif 'x' in query_params and 'y' in query_params:
        x = float(query_params['x'])
        y = float(query_params['y'])
        return x, y
    else:
        return None


def _convert_coords(lon, lat, orig_srid, dest_srid):
    """
    Convertes a point between two coordinates
    Parameters:
    lon - Longitude as float
    lat - Latitude as float
    original_srid - The int value of the point's srid
    dest_srid - The srid of the coordinate system to convert too

    Returns
    The new coordinates as a tuple. None if the convertion failed
    """
    p = Point(lon, lat, srid=orig_srid)
    p.transform(dest_srid)
    return p.coords