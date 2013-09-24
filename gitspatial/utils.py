def disk_size_format(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return '%3.1f %s' % (num, x)
        num /= 1024.0

def strip_zs(geojson_geometry):
    if geojson_geometry['type'] == 'Point':
        geojson_geometry['coordinates'] = geojson_geometry['coordinates'][:2]
    elif geojson_geometry['type'] == 'LineString':
        geojson_geometry['coordinates'] = [coord[:2] for coord in geojson_geometry['coordinates']]
    else:  # Polygon
        for i, coords_set in enumerate(geojson_geometry['coordinates']):
            geojson_geometry['coordinates'][i] = [coord[:2] for coord in coords_set]
    return geojson_geometry
