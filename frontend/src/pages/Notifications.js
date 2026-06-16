import React, { useEffect, useState } from 'react';
import { getNotifications, markAllNotificationsRead, markNotificationRead } from '../services/api';

const TYPE_META = {
  collect: { icon: '📥', color: '#38bdf8', label: 'Collecte' },
  training: { icon: '🧠', color: '#a78bfa', label: 'Entraînement' },
  subscription: { icon: '⭐', color: '#fbbf24', label: 'Abonnement' },
  payment: { icon: '💳', color: '#34d399', label: 'Paiement' },
  pdf_export: { icon: '📄', color: '#5271ff', label: 'Export PDF' },
  ticket: { icon: '🎫', color: '#fb923c', label: 'Ticket' },
  alert: { icon: '🔔', color: '#f87171', label: 'Alerte' },
  system: { icon: 'ℹ️', color: '#64748b', label: 'Système' },
};

function timeAgo(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr.replace(' ', 'T'));
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return "à l'instant";
    if (diff < 3600) return `il y a ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `il y a ${Math.floor(diff / 3600)} h`;
    return d.toLocaleDateString('fr-FR');
  } catch { return ''; }
}

export default function Notifications() {
  const [notifs, setNotifs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const load = () => {
    setLoading(true);
    getNotifications(100)
      .then((r) => setNotifs(r.data || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleReadAll = async () => {
    await markAllNotificationsRead();
    setNotifs((ns) => ns.map((n) => ({ ...n, read: true })));
    window.dispatchEvent(new Event('sentiflow:refresh-notifs'));
  };

  const handleClick = async (n) => {
    if (!n.read) {
      await markNotificationRead(n.id);
      setNotifs((ns) => ns.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
      window.dispatchEvent(new Event('sentiflow:refresh-notifs'));
    }
  };

  const types = ['all', ...Array.from(new Set(notifs.map((n) => n.type)))];
  const shown = filter === 'all' ? notifs : notifs.filter((n) => n.type === filter);
  const unread = notifs.filter((n) => !n.read).length;

  return (
    <div style={{ maxWidth: 760, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h1 style={{ marginBottom: 4 }}>Notifications</h1>
          <p style={{ color: '#64748b', fontSize: '0.85rem' }}>{unread} non lue(s)</p>
        </div>
        {unread > 0 && (
          <button className="btn-primary" onClick={handleReadAll} style={{ fontSize: '0.8rem' }}>
            Tout marquer comme lu
          </button>
        )}
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
        {types.map((t) => (
          <button key={t} onClick={() => setFilter(t)} style={{
            padding: '4px 10px', borderRadius: 12, fontSize: '0.74rem', cursor: 'pointer',
            background: filter === t ? '#5271ff' : '#f1f5f9', color: filter === t ? '#fff' : '#475569',
            border: '1px solid #e2e8f0',
          }}>
            {t === 'all' ? 'Tout' : (TYPE_META[t]?.label || t)}
          </button>
        ))}
      </div>

      {loading ? (
        <p style={{ color: '#64748b' }}>Chargement...</p>
      ) : shown.length === 0 ? (
        <p style={{ color: '#64748b', fontSize: '0.85rem' }}>Aucune notification.</p>
      ) : (
        <div style={{ display: 'grid', gap: 8 }}>
          {shown.map((n) => {
            const m = TYPE_META[n.type] || TYPE_META.system;
            return (
              <div key={n.id} onClick={() => handleClick(n)} style={{
                display: 'flex', gap: 12, padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
                background: n.read ? '#ffffff' : 'rgba(82,113,255,0.06)',
                border: `1px solid ${n.read ? '#e2e8f0' : '#5271ff44'}`,
              }}>
                <span style={{ fontSize: '1.2rem' }}>{m.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                    <strong style={{ fontSize: '0.88rem', color: '#1e293b' }}>{n.title}</strong>
                    <span style={{ fontSize: '0.7rem', color: '#94a3b8', whiteSpace: 'nowrap' }}>{timeAgo(n.created_at)}</span>
                  </div>
                  {n.message && <p style={{ fontSize: '0.8rem', color: '#475569', marginTop: 3 }}>{n.message}</p>}
                </div>
                {!n.read && <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#5271ff', marginTop: 6 }} />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
