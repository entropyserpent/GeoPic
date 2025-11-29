from flask import Flask, render_template, request, redirect, send_file, url_for, jsonify, Response
import os
import sys
import io
from datetime import datetime
from werkzeug.utils import secure_filename

# Ensure local modules can be imported when running from portable Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from exif_utils import extract_gps_datetime
from db import init_db, add_photo, get_photos, update_coords, delete_photo, clear_all, update_photo_metadata
from kmz_exporter import build_kmz
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic'}

app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

def allowed_file(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    photos = get_photos()
    return render_template('index.html', photos=photos)

@app.route('/map')
def map_view():
    return render_template('map.html')

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('photos')
    skipped = []
    for f in files:
        if not f or not f.filename:
            continue
        fname = secure_filename(f.filename)
        if not allowed_file(fname):
            continue
        dest = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        
        # Skip if file already exists
        if os.path.exists(dest):
            skipped.append(fname)
            continue
            
        f.save(dest)
        # Extract GPS + time
        lat, lng, taken_at = extract_gps_datetime(dest)
        add_photo({'filename': fname, 'path': dest, 'lat': lat, 'lng': lng, 'taken_at': taken_at})
    return redirect(url_for('index'))

@app.route('/export/kmz')
def export_kmz():
    photos = get_photos(only_with_gps=True)
    kmz_bytes = build_kmz(photos)
    return send_file(io.BytesIO(kmz_bytes), mimetype='application/vnd.google-earth.kmz', as_attachment=True, download_name=f'geopic_{datetime.now().strftime("%Y%m%d_%H%M%S")}.kmz')

@app.route('/associate', methods=['POST'])
def associate():
    data = request.get_json(force=True, silent=True) or {}
    filename = data.get('filename')
    lat = data.get('lat')
    lng = data.get('lng')
    if not filename or lat is None or lng is None:
        return jsonify({'ok': False, 'error': 'filename, lat, lng required'}), 400
    try:
        update_coords(filename, float(lat), float(lng))
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
    return jsonify({'ok': True})

@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json(force=True, silent=True) or {}
    filename = data.get('filename')
    if not filename:
        return jsonify({'ok': False, 'error': 'filename required'}), 400
    # Remove from DB
    delete_photo(filename)
    # Remove file
    try:
        upload_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(upload_path):
            os.remove(upload_path)
    except Exception:
        pass
    return jsonify({'ok': True})

@app.route('/clear_all', methods=['POST'])
def clear_all_photos():
    # Clear database
    clear_all()
    # Remove all files from uploads
    try:
        for fname in os.listdir(UPLOAD_FOLDER):
            fpath = os.path.join(UPLOAD_FOLDER, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
    except Exception:
        pass
    return jsonify({'ok': True})

@app.route('/api/photos')
def api_photos():
    photos = get_photos()
    return jsonify({'photos': photos})

@app.route('/export/geofence', methods=['POST'])
def export_geofence():
    data = request.json
    geofence = data.get('geofence')
    
    if not geofence:
        return jsonify({'error': 'No geofence'}), 400
    
    # Get all photos with GPS
    all_photos = get_photos(only_with_gps=True)
    
    # Filter photos inside geofence
    filtered = []
    for p in all_photos:
        if point_in_polygon(p['lat'], p['lng'], geofence):
            filtered.append(p)
    
    if not filtered:
        return jsonify({'error': 'No photos in geofence'}), 400
    
    # Build KMZ (images are always embedded)
    kmz_bytes = build_kmz(filtered)
    return send_file(
        io.BytesIO(kmz_bytes),
        mimetype='application/vnd.google-earth.kmz',
        as_attachment=True,
        download_name=f'geofence_{datetime.now().strftime("%Y%m%d_%H%M%S")}.kmz'
    )

def point_in_polygon(lat, lng, geofence):
    """Ray casting algorithm for point in polygon test."""
    coords = geofence['coordinates'][0]  # GeoJSON polygon
    x, y = lng, lat
    n = len(coords)
    inside = False
    
    p1x, p1y = coords[0]
    for i in range(n):
        p2x, p2y = coords[i]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
