'use client';

import { useEffect, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { supabase, isConfigured } from '../lib/supabase';

const Map = dynamic(() => import('../components/Map'), { ssr: false });

export default function Home() {
  const [potholes, setPotholes] = useState([]);
  const [severity, setSeverity] = useState('all');
  const [status, setStatus] = useState('all');
  const [days, setDays] = useState('all');
  const [view, setView] = useState('clusters');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    async function load() {
      if (isConfigured) {
        const { data, error } = await supabase
          .from('potholes')
          .select('*')
          .order('detected_at', { ascending: false })
          .limit(2000);
        if (!active) return;
        if (error) setError(error.message);
        else setPotholes(data || []);
      } else {
        // Fallback to local FastAPI server
        try {
          const res = await fetch('http://localhost:8000/potholes?limit=2000');
          if (res.ok) {
            const data = await res.json();
            const formatted = data.map((p) => ({
              ...p,
              image_url: p.image_url?.startsWith('/static')
                ? `http://localhost:8000${p.image_url}`
                : p.image_url,
            }));
            if (active) setPotholes(formatted);
          }
        } catch (e) {
          if (active) setError('Could not reach backend at http://localhost:8000');
        }
      }
    }
    load();

    if (isConfigured) {
      const channel = supabase
        .channel('potholes-live')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'potholes' }, (payload) => {
          setPotholes((prev) => [payload.new, ...prev.filter((p) => p.id !== payload.new.id)]);
        })
        .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'potholes' }, (payload) => {
          setPotholes((prev) => prev.map((p) => (p.id === payload.new.id ? payload.new : p)));
        })
        .subscribe();

      return () => {
        active = false;
        supabase.removeChannel(channel);
      };
    } else {
      const pollTimer = setInterval(load, 3000);
      return () => {
        active = false;
        clearInterval(pollTimer);
      };
    }
  }, []);

  const filtered = useMemo(() => {
    const cutoff = days === 'all' ? 0 : Date.now() - Number(days) * 86400000;
    return potholes.filter(
      (p) =>
        (severity === 'all' || p.severity === severity) &&
        (status === 'all' || p.status === status) &&
        new Date(p.detected_at).getTime() >= cutoff
    );
  }, [potholes, severity, status, days]);

  const stats = useMemo(() => {
    const count = (fn) => filtered.filter(fn).length;
    return {
      total: filtered.length,
      open: count((p) => p.status === 'open'),
      high: count((p) => p.severity === 'high' && p.status !== 'fixed'),
      fixed: count((p) => p.status === 'fixed'),
    };
  }, [filtered]);

  async function onStatusChange(id, newStatus) {
    if (!password) {
      setError('Enter the admin password in the sidebar to change status');
      return;
    }
    const res = await fetch('/api/status', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-admin-password': password },
      body: JSON.stringify({ id, status: newStatus }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setError(body.error || 'Update failed');
      return;
    }
    setError('');
    setPotholes((prev) => prev.map((p) => (p.id === id ? { ...p, status: newStatus } : p)));
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>Nashik Road Hazards</h1>
        <p className="sub">Live pothole detections from city buses</p>

        <div className="stats">
          <div className="stat"><b>{stats.total}</b><span>Shown</span></div>
          <div className="stat"><b>{stats.open}</b><span>Open</span></div>
          <div className="stat"><b>{stats.high}</b><span>High severity, unfixed</span></div>
          <div className="stat"><b>{stats.fixed}</b><span>Fixed</span></div>
        </div>

        <label>Map view</label>
        <select value={view} onChange={(e) => setView(e.target.value)}>
          <option value="clusters">Clustered markers</option>
          <option value="markers">All markers</option>
          <option value="heat">Heatmap</option>
        </select>

        <label>Severity</label>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="all">All</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <label>Status</label>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="all">All</option>
          <option value="open">Open</option>
          <option value="in_progress">In progress</option>
          <option value="fixed">Fixed</option>
        </select>

        <label>Time range</label>
        <select value={days} onChange={(e) => setDays(e.target.value)}>
          <option value="all">All time</option>
          <option value="1">Last 24 hours</option>
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
        </select>

        <label>Admin password (to change status)</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />

        {error && <p style={{ color: '#dc2626', fontSize: 12, marginTop: 8 }}>{error}</p>}

        <div className="legend">
          <div><span className="dot" style={{ background: '#dc2626' }} /> High</div>
          <div><span className="dot" style={{ background: '#f97316' }} /> Medium</div>
          <div><span className="dot" style={{ background: '#eab308' }} /> Low</div>
          <div><span className="dot" style={{ background: '#6b7280' }} /> Fixed</div>
        </div>
      </aside>

      <main className="mapwrap">
        <Map potholes={filtered} onStatusChange={onStatusChange} view={view} />
      </main>
    </div>
  );
}
