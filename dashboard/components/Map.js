'use client';

import { useEffect } from 'react';
import L from 'leaflet';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';

const COLORS = { low: '#eab308', medium: '#f97316', high: '#dc2626' };
const WEIGHTS = { low: 0.3, medium: 0.6, high: 1.0 };

function colorFor(p) {
  if (p.status === 'fixed') return '#6b7280';
  return COLORS[p.severity] || '#dc2626';
}

function HeatLayer({ points }) {
  const map = useMap();

  useEffect(() => {
    let layer = null;
    let cancelled = false;

    (async () => {
      if (typeof window !== 'undefined') {
        window.L = L;
        await import('leaflet.heat');
        if (cancelled) return;
        const data = points
          .filter((p) => p.status !== 'fixed')
          .map((p) => [parseFloat(p.lat), parseFloat(p.lon), WEIGHTS[p.severity] || 0.5]);
        
        if (typeof L.heatLayer === 'function') {
          layer = L.heatLayer(data, { radius: 25, blur: 20, maxZoom: 17 }).addTo(map);
        }
      }
    })();

    return () => {
      cancelled = true;
      if (layer && map) {
        try {
          map.removeLayer(layer);
        } catch (e) {}
      }
    };
  }, [points, map]);

  return null;
}

function PotholeMarker({ p, onStatusChange }) {
  return (
    <CircleMarker
      center={[parseFloat(p.lat), parseFloat(p.lon)]}
      radius={p.severity === 'high' ? 10 : p.severity === 'medium' ? 8 : 6}
      pathOptions={{
        color: colorFor(p),
        fillColor: colorFor(p),
        fillOpacity: p.status === 'fixed' ? 0.4 : 0.8,
      }}
    >
      <Popup>
        <div className="popup">
          <img src={p.image_url} alt="pothole" />
          <p><b>Severity:</b> <span style={{ textTransform: 'uppercase', color: colorFor(p), fontWeight: 'bold' }}>{p.severity}</span></p>
          <p><b>Confidence:</b> {(p.confidence * 100).toFixed(0)}%</p>
          <p><b>Potholes in frame:</b> {p.pothole_count || 1}</p>
          <p><b>Detected:</b> {new Date(p.detected_at).toLocaleString()}</p>
          <p><b>Bus:</b> {p.device_id}</p>
          <p>
            <a href={`https://www.google.com/maps?q=${p.lat},${p.lon}`} target="_blank" rel="noreferrer">
              Open in Google Maps
            </a>
          </p>
          <select value={p.status || 'open'} onChange={(e) => onStatusChange(p.id, e.target.value)}>
            <option value="open">Open</option>
            <option value="in_progress">In progress</option>
            <option value="fixed">Fixed</option>
          </select>
        </div>
      </Popup>
    </CircleMarker>
  );
}

export default function Map({ potholes, onStatusChange, view }) {
  return (
    <MapContainer center={[19.9975, 73.7898]} zoom={13} scrollWheelZoom style={{ height: '100%', width: '100%' }}>
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {view === 'heat' && <HeatLayer points={potholes} />}
      {view === 'clusters' && (
        <MarkerClusterGroup chunkedLoading maxClusterRadius={50}>
          {potholes.map((p) => (
            <PotholeMarker key={p.id} p={p} onStatusChange={onStatusChange} />
          ))}
        </MarkerClusterGroup>
      )}
      {view === 'markers' &&
        potholes.map((p) => <PotholeMarker key={p.id} p={p} onStatusChange={onStatusChange} />)}
    </MapContainer>
  );
}
