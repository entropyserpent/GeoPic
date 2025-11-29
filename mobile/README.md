GeoPic Mobile (Expo)
=====================

This is an Expo-based mobile companion for the GeoPic Flask server. It provides a minimal camera capture, local queue, and upload settings for testing on Android/iOS via Expo Go.

Quick start
-----------

Prerequisites:
- Node.js and npm
- `npx` (comes with npm)
- Expo Go on your phone (for quick testing)

Run locally:

```powershell
cd mobile
npm install
npx expo start
```

Then open the project in Expo Go (scan the QR code) or run on an emulator via `npx expo run:android` / `npx expo run:ios`.

Configuration
- Configure the server URL and API token inside the app Settings screen.

Notes
- This is a minimal scaffold. The `App.js` implements a simple Camera + Queue + Settings UI. For production use you should enable HTTPS on the server and store secrets in a secure store.
