import React, { useEffect, useState } from 'react';
import { getTargets, createTarget, deleteTarget, collectTweets, analyzeTweets } from '../services/api';
import { Plus, Trash2, Download, Cpu, Loader2, Clock } from 'lucide-react';

function CountdownTimer() {
  const [timeLeft, setTimeLeft] = useState('');
  const [active, setActive] = useState(true);
  const [interval, setIntervalMin] = useState(15);

  useEffect(() => {
    const checkStatus = () => {
      fetch('/admin/collect-timer')
        .then((r) => r.json())
        .then((d) => { setActive(d.active !== false); setIntervalMin(d.interval_minutes || 15); })
        .catch(() => {});
    };
    checkStatus();
    const statusId = setInterval(checkStatus, 10000);
    const onRefresh = () => checkStatus();
    window.addEventListener('sentiflow:refresh-timer', onRefresh);
    return () => { clearInterval(statusId); window.removeEventListener('sentiflow:refresh-timer', onRefresh); };
  }, []);

  useEffect(() => {
    if (!active) { setTimeLeft(''); return; }
    const update = () => {
      const now = new Date();
      const totalSec = now.getMinutes() * 60 + now.getSeconds();
      const intervalSec = interval * 60;
      const remaining = intervalSec - (totalSec % intervalSec);
      const min = Math.floor(remaining / 60);
      const sec = remaining % 60;
      setTimeLeft(`${min}:${sec.toString().padStart(2, '0')}`);
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, [active, interval]);

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '8px 14px', background: '#ffffff', border: '1px solid #e2e8f0',
      borderRadius: 8, fontSize: '0.78rem', color: '#64748b',
    }}>
      <Clock size={14} color={active ? '#5271ff' : '#64748b'} />
      {active ? (
        <span>Prochaine collecte automatique dans <strong style={{ color: '#1e293b' }}>{timeLeft}</strong> (toutes les {interval} min)</span>
      ) : (
        <span>Collecte automatique <strong style={{ color: '#fbbf24' }}>en pause</strong> — utilisez « Collecter » manuellement</span>
      )}
    </div>
  );
}

export default function Cibles() {
  const [targets, setTargets] = useState([]);
  const [name, setName] = useState('');
  const [type, setType] = useState('hashtag');
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState({});
  const [message, setMessage] = useState('');

  const loadTargets = () => {
    getTargets().then((res) => setTargets(res.data)).catch(() => {});
  };

  useEffect(() => { loadTargets(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    try {
      await createTarget({ name: name.trim(), target_type: type });
      setName('');
      loadTargets();
      setMessage('Cible creee');
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Erreur');
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Supprimer cette cible ?')) return;
    try {
      await deleteTarget(id);
      loadTargets();
    } catch (err) {
      setMessage('Erreur suppression');
    }
  };

  const handleCollect = async (id) => {
    setActionLoading((prev) => ({ ...prev, [`collect_${id}`]: true }));
    try {
      const res = await collectTweets(id);
      setMessage(`${res.data.saved || res.data.tweets_saved || 0} tweets collectes`);
      loadTargets();
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Erreur collecte');
    } finally {
      setActionLoading((prev) => ({ ...prev, [`collect_${id}`]: false }));
      setTimeout(() => setMessage(''), 4000);
    }
  };

  const handleAnalyze = async (id) => {
    setActionLoading((prev) => ({ ...prev, [`analyze_${id}`]: true }));
    try {
      const res = await analyzeTweets(id);
      setMessage(`${res.data.analyzed || 0} tweets analyses`);
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Erreur analyse');
    } finally {
      setActionLoading((prev) => ({ ...prev, [`analyze_${id}`]: false }));
      setTimeout(() => setMessage(''), 4000);
    }
  };

  const btnStyle = {
    padding: '6px 10px',
    border: '1px solid #e2e8f0',
    background: 'transparent',
    color: '#475569',
    borderRadius: 6,
    fontSize: '0.78rem',
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
  };

  return (
    <div style={{ maxWidth: 700 }}>
      <h1 style={{ marginBottom: 4 }}>Cibles</h1>
      <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: 24 }}>
        Les hashtags et comptes que vous suivez. SentiFlow y collecte les tweets (manuellement ou
        automatiquement) puis les analyse. Toutes les autres pages (Dashboard, Assistant, Alertes)
        se basent sur ces cibles.
      </p>

      {/* Timer */}
      <CountdownTimer />

      {/* Form */}
      <form onSubmit={handleCreate} style={{ display: 'flex', gap: 10, marginBottom: 24, marginTop: 16 }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="#hashtag ou @compte"
          style={{
            flex: 1,
            padding: '10px 14px',
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: 8,
            color: '#0f172a',
            fontSize: '0.88rem',
            outline: 'none',
          }}
        />
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          style={{
            padding: '10px 14px',
            background: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: 8,
            color: '#1e293b',
            fontSize: '0.88rem',
          }}
        >
          <option value="hashtag">Hashtag</option>
          <option value="account">Compte</option>
        </select>
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '10px 16px',
            background: '#5271ff',
            color: 'white',
            border: 'none',
            borderRadius: 8,
            fontWeight: 600,
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <Plus size={16} /> Ajouter
        </button>
      </form>

      {message && (
        <div style={{
          padding: '10px 14px',
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: 8,
          marginBottom: 16,
          fontSize: '0.82rem',
          color: '#475569',
        }}>
          {message}
        </div>
      )}

      {/* List */}
      <div>
        {targets.map((target) => (
          <div
            key={target.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 16px',
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: 10,
              marginBottom: 8,
            }}
          >
            <div>
              <span style={{ color: '#0f172a', fontWeight: 500, fontSize: '0.9rem' }}>
                {target.name}
              </span>
              <span style={{ marginLeft: 10, color: '#94a3b8', fontSize: '0.75rem' }}>
                {target.target_type}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                onClick={() => handleCollect(target.id)}
                disabled={actionLoading[`collect_${target.id}`]}
                style={btnStyle}
              >
                {actionLoading[`collect_${target.id}`] ? <Loader2 size={13} /> : <Download size={13} />}
                Collecter
              </button>
              <button
                onClick={() => handleAnalyze(target.id)}
                disabled={actionLoading[`analyze_${target.id}`]}
                style={btnStyle}
              >
                {actionLoading[`analyze_${target.id}`] ? <Loader2 size={13} /> : <Cpu size={13} />}
                Analyser
              </button>
              <button
                onClick={() => handleDelete(target.id)}
                style={{ ...btnStyle, color: '#f87171', borderColor: '#3f1f1f' }}
              >
                <Trash2 size={13} />
              </button>
            </div>
          </div>
        ))}

        {targets.length === 0 && (
          <p style={{ color: '#94a3b8', textAlign: 'center', padding: 30, fontSize: '0.88rem' }}>
            Aucune cible. Ajoute un hashtag ou un compte pour commencer.
          </p>
        )}
      </div>
    </div>
  );
}
