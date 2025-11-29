from typing import Optional, Tuple
import exifread
from datetime import datetime

# Convert EXIF GPS rational values to decimal degrees
# EXIF stores as degrees, minutes, seconds (tuples of rationals)

def _ratio_to_float(r):
    try:
        return float(r.num) / float(r.den)
    except Exception:
        return float(r)

def _dms_to_dd(dms, ref: str) -> float:
    d = _ratio_to_float(dms[0])
    m = _ratio_to_float(dms[1])
    s = _ratio_to_float(dms[2])
    dd = d + (m / 60.0) + (s / 3600.0)
    if ref in ['S', 'W']:
        dd = -dd
    return dd


def extract_gps_datetime(file_path: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    lat = lng = None
    taken_at = None
    with open(file_path, 'rb') as f:
        tags = exifread.process_file(f, details=False)
    lat_tag = tags.get('GPS GPSLatitude')
    lat_ref = tags.get('GPS GPSLatitudeRef')
    lng_tag = tags.get('GPS GPSLongitude')
    lng_ref = tags.get('GPS GPSLongitudeRef')
    dt_tag = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
    if lat_tag and lat_ref and lng_tag and lng_ref:
        try:
            lat = _dms_to_dd(lat_tag.values, str(lat_ref.values))
            lng = _dms_to_dd(lng_tag.values, str(lng_ref.values))
        except Exception:
            lat = None
            lng = None
    if dt_tag:
        try:
            # EXIF format: YYYY:MM:DD HH:MM:SS
            dt = datetime.strptime(str(dt_tag.values), '%Y:%m:%d %H:%M:%S')
            taken_at = dt.isoformat(sep=' ', timespec='seconds')
        except Exception:
            taken_at = str(dt_tag.values)
    return lat, lng, taken_at
