import zipfile
import io
import os
from typing import List, Dict, Any


def build_kmz(photos: List[Dict[str, Any]]) -> bytes:
    """Build KMZ containing KML and embedded images for waypoints.
    Each placemark includes an <img> referencing an embedded file.
    """
    # Build KML in memory
    kml_lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        "<kml xmlns='http://www.opengis.net/kml/2.2' xmlns:gx='http://www.google.com/kml/ext/2.2'>",
        "<Document><name>GeoPic Export</name>"
    ]

    for p in photos:
        lat = p.get('lat'); lng = p.get('lng'); name = p.get('filename'); path = p.get('path')
        if lat is None or lng is None or not name:
            continue
        # Reference embedded image path under images/
        img_rel = f"images/{name}"
        desc_html = f"<p><img src='{img_rel}' style='max-width:480px'></p>"  # show the image
        if p.get('taken_at'):
            desc_html += f"<p><small>{p['taken_at']}</small></p>"
        kml_lines.append(
            f"<Placemark><name>{name}</name><description><![CDATA[{desc_html}]]></description>"
            f"<Point><coordinates>{lng},{lat},0</coordinates></Point></Placemark>"
        )

    kml_lines.append("</Document></kml>")
    kml_data = "".join(kml_lines)

    # Build KMZ zip with KML and embedded images
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('doc.kml', kml_data)
        for p in photos:
            name = p.get('filename'); path = p.get('path')
            if not name or not path:
                continue
            if not os.path.isfile(path):
                continue
            # Write image bytes into images/<filename>
            try:
                with open(path, 'rb') as rf:
                    zf.writestr(f"images/{name}", rf.read())
            except Exception:
                # skip unreadable files
                pass
    mem.seek(0)
    return mem.read()
