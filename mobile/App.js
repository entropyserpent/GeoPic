import React, { useState, useEffect, useRef } from 'react';
import { View, Text, Button, TouchableOpacity, Image, FlatList, TextInput, StyleSheet, Alert, ScrollView } from 'react-native';
import * as FileSystem from 'expo-file-system';
import * as Location from 'expo-location';
import * as SecureStore from 'expo-secure-store';
import { Camera } from 'expo-camera';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImageManipulator from 'expo-image-manipulator';
import { WebView } from 'react-native-webview';

const QUEUE_KEY = 'geopic_queue_v1';
const SERVER_URL_KEY = 'geopic_server_url';
const TOKEN_KEY = 'geopic_token';
const LAST_SYNC_KEY = 'geopic_last_sync_v1';

export default function App() {
  const [screen, setScreen] = useState('camera');
  const [hasCameraPermission, setHasCameraPermission] = useState(null);
  const [hasLocationPermission, setHasLocationPermission] = useState(null);
  const cameraRef = useRef(null);
  const [queue, setQueue] = useState([]);
  const [serverUrl, setServerUrl] = useState('http://YOUR_PC_IP:5000');
  const [token, setToken] = useState('');
  const [isCameraReady, setCameraReady] = useState(false);

  useEffect(() => {
    (async () => {
      const cameraStatus = await Camera.requestCameraPermissionsAsync();
      setHasCameraPermission(cameraStatus.status === 'granted');
      const locStatus = await Location.requestForegroundPermissionsAsync();
      setHasLocationPermission(locStatus.status === 'granted');
      loadQueue();
      loadSettings();
    })();
  }, []);

  useEffect(() => {
    // load last sync time
    (async () => {
      try {
        const s = await AsyncStorage.getItem(LAST_SYNC_KEY);
        if (s) {
          // no-op for now; we keep as string when needed
        }
      } catch (e) { }
    })();
  }, []);

  async function loadSettings() {
    try {
      const url = await SecureStore.getItemAsync(SERVER_URL_KEY);
      const t = await SecureStore.getItemAsync(TOKEN_KEY);
      if (url) setServerUrl(url);
      if (t) setToken(t);
    } catch (err) {
      console.warn('Failed loading settings', err);
    }
  }

  async function saveSettings() {
    try {
      await SecureStore.setItemAsync(SERVER_URL_KEY, serverUrl || '');
      await SecureStore.setItemAsync(TOKEN_KEY, token || '');
      Alert.alert('Saved');
    } catch (err) {
      Alert.alert('Failed to save settings');
    }
  }

  async function loadQueue() {
    try {
      const raw = await AsyncStorage.getItem(QUEUE_KEY);
      const q = raw ? JSON.parse(raw) : [];
      setQueue(q);
    } catch (err) {
      console.warn('loadQueue', err);
    }
  }

  async function persistQueue(newQueue) {
    setQueue(newQueue);
    await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(newQueue));
  }

  async function saveLastSync(ts) {
    try {
      await AsyncStorage.setItem(LAST_SYNC_KEY, ts);
    } catch (e) { }
  }

  async function getLastSync() {
    try {
      const s = await AsyncStorage.getItem(LAST_SYNC_KEY);
      return s;
    } catch (e) { return null; }
  }

  const [serverPhotos, setServerPhotos] = useState([]);

  async function syncServerPhotos() {
    if (!serverUrl) {
      Alert.alert('Set server URL first');
      return;
    }
    try {
      const last = await getLastSync();
      const q = last ? `?since=${encodeURIComponent(last)}` : '';
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const resp = await fetch((serverUrl || '').replace(/\/$/, '') + '/api/photos' + q, { headers });
      if (!resp.ok) throw new Error(await resp.text());
      const data = await resp.json();
      const photos = data.photos || [];
      setServerPhotos(photos);
      const now = new Date().toISOString();
      await saveLastSync(now);
      Alert.alert('Sync complete', `${photos.length} photos found`);
    } catch (err) {
      console.error('sync', err);
      Alert.alert('Sync failed', String(err));
    }
  }

  async function importServerPhoto(p) {
    try {
      const url = p.url || p.path || '';
      const filename = p.filename || url.split('/').pop() || makeFilename();
      const dest = FileSystem.documentDirectory + filename;
      await FileSystem.downloadAsync(url, dest);
      const record = {
        id: 'srv-' + Date.now().toString(),
        filename,
        localUri: dest,
        lat: p.lat || null,
        lng: p.lng || null,
        taken_at: p.taken_at || new Date().toISOString(),
        status: 'synced'
      };
      const newQueue = [record, ...(queue || [])];
      await persistQueue(newQueue);
      Alert.alert('Imported', filename);
    } catch (err) {
      console.error('import', err);
      Alert.alert('Import failed', String(err));
    }
  }

  function makeFilename() {
    const t = new Date().toISOString().replace(/[:.]/g, '-');
    return `photo-${t}.jpg`;
  }

  async function captureAndSave() {
    if (!cameraRef.current) return;
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.6 });
      // optional resize / fix orientation
      const manipulated = await ImageManipulator.manipulateAsync(photo.uri, [], { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG });
      const filename = makeFilename();
      const dest = FileSystem.documentDirectory + filename;
      await FileSystem.copyAsync({ from: manipulated.uri, to: dest });

      let loc = null;
      if (hasLocationPermission) {
        const l = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
        loc = { lat: l.coords.latitude, lng: l.coords.longitude };
      }

      const record = {
        id: Date.now().toString(),
        filename,
        localUri: dest,
        lat: loc ? loc.lat : null,
        lng: loc ? loc.lng : null,
        taken_at: new Date().toISOString(),
        status: 'pending'
      };

      const newQueue = [record, ...(queue || [])];
      await persistQueue(newQueue);
      Alert.alert('Saved', 'Photo saved to queue');
    } catch (err) {
      console.error('capture error', err);
      Alert.alert('Capture failed', String(err));
    }
  }

  async function uploadRecord(rec) {
    try {
      const form = new FormData();
      form.append('file', {
        uri: rec.localUri,
        name: rec.filename,
        type: 'image/jpeg'
      });
      if (rec.lat != null) form.append('lat', String(rec.lat));
      if (rec.lng != null) form.append('lng', String(rec.lng));
      if (rec.taken_at) form.append('taken_at', rec.taken_at);

      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const resp = await fetch((serverUrl || '').replace(/\/$/, '') + '/api/upload-photo', {
        method: 'POST',
        body: form,
        headers
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`Upload failed: ${resp.status} ${text}`);
      }
      // success -> update queue
      const updated = queue.map(q => q.id === rec.id ? { ...q, status: 'synced' } : q);
      await persistQueue(updated);
      Alert.alert('Uploaded', rec.filename);
    } catch (err) {
      console.error('upload', err);
      const updated = queue.map(q => q.id === rec.id ? { ...q, status: 'failed' } : q);
      await persistQueue(updated);
      Alert.alert('Upload error', String(err));
    }
  }

  async function uploadAll() {
    for (const r of queue) {
      if (r.status !== 'synced' && r.status !== 'uploading') {
        const updating = queue.map(q => q.id === r.id ? { ...q, status: 'uploading' } : q);
        await persistQueue(updating);
        // small await to let UI update
        await uploadRecord(r);
      }
    }
  }

  function renderCamera() {
    if (hasCameraPermission === false) {
      return <View style={styles.center}><Text>No camera permission</Text></View>;
    }
    return (
      <View style={{ flex: 1 }}>
        <Camera style={{ flex: 1 }} ref={cameraRef} onCameraReady={() => setCameraReady(true)} />
        <View style={styles.cameraControls}>
          <Button title="Capture" onPress={captureAndSave} disabled={!isCameraReady} />
          <Button title="Open Queue" onPress={() => setScreen('queue')} />
        </View>
      </View>
    );
  }

  function renderQueue() {
    return (
      <View style={{ flex: 1, padding: 8 }}>
        <Button title="Back to Camera" onPress={() => setScreen('camera')} />
        <Button title="Upload All" onPress={uploadAll} />
        <Button title="Sync From Server" onPress={syncServerPhotos} />
        <FlatList
          data={queue}
          keyExtractor={(i) => i.id}
          renderItem={({ item }) => (
            <View style={styles.queueItem}>
              <Image source={{ uri: item.localUri }} style={styles.thumb} />
              <View style={{ flex: 1 }}>
                <Text>{item.filename}</Text>
                <Text>Status: {item.status}</Text>
                <View style={{ flexDirection: 'row' }}>
                  <Button title="Upload" onPress={() => uploadRecord(item)} />
                  <Button title="Delete" onPress={async () => {
                    const filtered = queue.filter(q => q.id !== item.id);
                    try { await FileSystem.deleteAsync(item.localUri); } catch (e) { }
                    await persistQueue(filtered);
                  }} />
                </View>
              </View>
            </View>
          )}
        />

        {serverPhotos && serverPhotos.length > 0 && (
          <View style={{ marginTop: 12 }}>
            <Text style={{ fontWeight: 'bold' }}>Server Photos</Text>
            <FlatList
              data={serverPhotos}
              keyExtractor={(i) => (i.filename || i.url || Math.random()).toString()}
              renderItem={({ item }) => (
                <View style={styles.queueItem}>
                  <Image source={{ uri: item.url || item.path }} style={styles.thumb} />
                  <View style={{ flex: 1 }}>
                    <Text>{item.filename || item.url}</Text>
                    <Text>{item.taken_at}</Text>
                    <View style={{ flexDirection: 'row' }}>
                      <Button title="Import" onPress={() => importServerPhoto(item)} />
                    </View>
                  </View>
                </View>
              )}
            />
          </View>
        )}
      </View>
    );
  }

  function renderSettings() {
    return (
      <ScrollView style={{ padding: 12 }}>
        <Text>Server URL</Text>
        <TextInput style={styles.input} value={serverUrl} onChangeText={setServerUrl} />
        <Text>API Token (optional)</Text>
        <TextInput style={styles.input} value={token} onChangeText={setToken} secureTextEntry />
        <Button title="Save Settings" onPress={saveSettings} />
        <Text style={{ marginTop: 12, color: '#666' }}>Note: use your PC LAN IP, for example: http://192.168.1.12:5000</Text>
      </ScrollView>
    );
  }

  return (
    <View style={{ flex: 1 }}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => setScreen('camera')} style={styles.tab}><Text>Camera</Text></TouchableOpacity>
        <TouchableOpacity onPress={() => setScreen('queue')} style={styles.tab}><Text>Queue ({queue.length})</Text></TouchableOpacity>
        <TouchableOpacity onPress={() => setScreen('map')} style={styles.tab}><Text>Map</Text></TouchableOpacity>
        <TouchableOpacity onPress={() => setScreen('settings')} style={styles.tab}><Text>Settings</Text></TouchableOpacity>
      </View>
      <View style={{ flex: 1 }}>
        {screen === 'camera' && renderCamera()}
        {screen === 'queue' && renderQueue()}
        {screen === 'settings' && renderSettings()}
        {screen === 'map' && (
          <WebView
            source={{ uri: (serverUrl || '').replace(/\/$/, '') + '/map', headers: token ? { Authorization: `Bearer ${token}` } : {} }}
            style={{ flex: 1 }}
          />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  topBar: { flexDirection: 'row', paddingTop: 40, backgroundColor: '#eee', justifyContent: 'space-around' },
  tab: { padding: 10 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  cameraControls: { flexDirection: 'row', justifyContent: 'space-around', padding: 8, backgroundColor: '#fff' },
  queueItem: { flexDirection: 'row', padding: 8, borderBottomWidth: 1, borderColor: '#ddd' },
  thumb: { width: 80, height: 80, marginRight: 8 },
  input: { borderWidth: 1, borderColor: '#ccc', padding: 8, marginBottom: 12 }
});
