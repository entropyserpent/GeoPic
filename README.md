Yet can you attempt to detect node dot JS. I just installed# GeoPic

A simple Flask app to upload images, read GPS from EXIF, manually set coordinates when missing, and export a KMZ with embedded images as placemarks.

## Quick Start (existing Python)

```powershell
cd C:\Users\Kenny\Projects\GeoPic
C:\Users\Kenny\AppData\Local\Python\pythoncore-3.14-64\python.exe run_geopic.py
```
- First run installs deps from `requirements.txt`, then starts the server.
- Open `http://127.0.0.1:5000`.

## Portable USB Start (no system Python)

1. Download Windows embeddable Python (64-bit) ZIP from python.org.
2. Unzip into `GeoPic\python\` so `GeoPic\python\python.exe` exists.
3. Double-click `GeoPic\start.cmd`.

The script installs dependencies and starts the server at `http://127.0.0.1:5000`.

## Features
- Upload multiple images to `uploads/`.
- Extract GPS and capture time from EXIF automatically.
- Set GPS manually in a modal with a mini map (Leaflet).
- Export KMZ with images embedded under `images/`, each photo as a placemark popup.

## Structure
- `app.py` — Flask web app
- `db.py` — SQLite (photos.db)
- `exif_utils.py` — EXIF parsing for GPS + datetime
- `kmz_exporter.py` — KMZ builder (embeds images)
- `templates/` — HTML UI (Bootstrap)
- `uploads/` — Uploaded files
- `requirements.txt` — Dependencies
- `run_geopic.py` — One-file launcher using your current Python
- `start.cmd` — Portable launcher using `python\python.exe`

## Tips
- LAN access: bind is already `0.0.0.0` in `app.py`; browse via your PC IP.
- If port 5000 is blocked, edit `app.py` to change `port=5000`.
- KMZ opens in Google Earth; each placemark shows the embedded image.
