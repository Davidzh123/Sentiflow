import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { RefreshCw, Play, Square, Database, Cpu, Users, BarChart3, Loader2 } from 'lucide-react';

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [dbOverview, setDbOverview] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [trainingStats, setTrainingStats] = useState(null);
  const [loading, setLoading] = useState({});
  const [message, setMessage] = useState('');

  const loadAll = async () => {
    try {
      const [statsRes, dbRes, schedRes, pipeRes, trainRes] = await Promise.allSettled([
        api.get('/admin/stats'),
        api.get('/admin/db/overview'),
        api.get('/admin/celery/schedule'),
        api.get('/admin/pipeline/status'),
        api.get('/admin/training-data/stats'),
      ]);
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      if (dbRes.status === 'fulfilled') setDbOverview(dbRes.value.data);
      if (schedRes.status === 'fulfilled') setSchedule(schedRes.value.data);
      if (pipeRes.status === 'fulfilled') setPipelineStatus(pipeRes.value.data);
      if (trainRes.status === 'fulfilled') setTrainingStats(trainRes.value.data);
    } catch (err) {
      setMessage('Erreur chargement admin');
    }
  };

  useEffect(() => { loadAll(); }, []);

  const doAction = async (key, fn) => {
    setLoading((prev) => ({ ...prev, [key]: true }));
    setMessage('');
    try {
      const res = await fn();
      setMessage(res.data?.message || 'OK');
      loadAll();
    } catch (err) {
      setMessage(err?.response?.data?.detail || 'Erreur');
    } finally {
      setLoading((prev) => ({ ...prev, [key]: false }));
    }
  };

  const cardStyle = { background: '#0f0f12', border: '1px solid #1c1c22', borderRadius: 12, padding: 20 };
  const labelStyle = { color: '#52525b', fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em' };
  const valueStyle = { color: '#fafafa', fontSize: '1.5rem', fontWeight: 700 };
  const btnStyle = (color = '#5271ff') => ({
    padding: '8px 14px', background: 'transparent', border: `1px solid ${color}33`,
    borderRadius: 6, color, fontSize: '0.78rem', fontWeight: 500,
    display: 'inline-flex', alignItems: 'center', gap: 6, cursor: 'pointer',
  });

  return (
    <div className="animate-in" style={{ maxWidth: 900 }}>
      <h1 style={{ marginBottom: 4 }}>Administration</h1>
      <p style={{ color: '#52525b', fontSize: '0.85rem', marginBottom: 28 }}>
        Controle complet : pipeline, collecte, analyse, BDD
      </p>

      {message && (
        <div style={{ padding: '10px 14px', background: '#0f0f12', border: '1px solid #27272a', borderRadius: 8, marginBottom: 16, fontSize: '0.82rem', color: '#a1a1aa' }}>
          {message}
        </div>
      )}

      {/* Vue d'ensemble BDD */}
      {dbOverview && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 28 }}>
          <div style={cardStyle}>
            <p style={labelStyle}>Tweets total</p>
            <p style={valueStyle}>{dbOverview.tweets?.total || 0}</p>
            <p style={{ color: '#71717a', fontSize: '0.72rem' }}>{dbOverview.tweets?.pending || 0} en attente</p>
          </div>
          <div style={cardStyle}>
            <p style={labelStyle}>Analyses</p>
            <p style={valueStyle}>{dbOverview.tweets?.analyzed || 0}</p>
          </div>
          <div style={cardStyle}>
            <p style={labelStyle}>Cibles</p>
            <p style={valueStyle}>{dbOverview.targets || 0}</p>
          </div>
          <div style={cardStyle}>
            <p style={labelStyle}>Utilisateurs</p>
            <p style={valueStyle}>{dbOverview.users || 0}</p>
          </div>
        </div>
      )}

      {/* Celery / Collecte */}
      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: '1.1rem', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
          <RefreshCw size={18} color="#5271ff" /> Collecte et Analyse (Celery)
        </h2>
        <div style={cardStyle}>
          {schedule && (
            <div style={{ marginBottom: 16 }}>
              <p style={{ color: '#a1a1aa', fontSize: '0.82rem', marginBottom: 8 }}>Schedule actuel :</p>
              {Object.entries(schedule).map(([name, config]) => (
                <div key={name} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #1c1c22' }}>
                  <span style={{ color: '#e4e4e7', fontSize: '0.82rem' }}>{name}</span>
                  <span style={{ color: '#71717a', fontSize: '0.78rem' }}>
                    {typeof config.interval_minutes === 'number' ? `${config.interval_minutes} min` : config.interval_minutes}
                  </span>
                </div>
              ))}
            </div>
          )}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button style={btnStyle('#5271ff')} onClick={() => doAction('collect', () => api.post('/admin/celery/collect-now'))} disabled={loading.collect}>
              {loading.collect ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={14} />} Collecter maintenant
            </button>
            <button style={btnStyle('#5271ff')} onClick={() => doAction('analyze', () => api.post('/admin/celery/analyze-now'))} disabled={loading.analyze}>
              {loading.analyze ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Cpu size={14} />} Analyser maintenant
            </button>
            <button style={btnStyle('#f87171')} onClick={() => doAction('stop', () => api.post('/admin/celery/stop-collect'))}>
              <Square size={14} /> Stopper collecte auto
            </button>
            <select
              id="interval-select"
              defaultValue="15"
              style={{ padding: '6px 10px', background: '#09090b', border: '1px solid #27272a', borderRadius: 6, color: '#e4e4e7', fontSize: '0.78rem' }}
            >
              <option value="5">5 min</option>
              <option value="10">10 min</option>
              <option value="15">15 min</option>
              <option value="30">30 min</option>
              <option value="60">1h</option>
              <option value="120">2h</option>
            </select>
            <button style={btnStyle('#34d399')} onClick={() => {
              const val = document.getElementById('interval-select').value;
              doAction('start', () => api.post(`/admin/celery/start-collect?interval_minutes=${val}`));
            }}>
              <Play size={14} /> Reactiver
            </button>
          </div>
        </div>
      </section>

      {/* Pipeline TinyGPT */}
      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: '1.1rem', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Cpu size={18} color="#5271ff" /> Pipeline TinyGPT (Entrainement)
        </h2>
        <div style={cardStyle}>
          {pipelineStatus?.last_eval && (
            <div style={{ marginBottom: 16 }}>
              <p style={{ color: '#a1a1aa', fontSize: '0.82rem', marginBottom: 8 }}>Dernier entrainement :</p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                <div>
                  <p style={labelStyle}>Score ancien</p>
                  <p style={{ color: '#e4e4e7', fontSize: '1rem', fontWeight: 600 }}>{(pipelineStatus.last_eval.old_score * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <p style={labelStyle}>Score nouveau</p>
                  <p style={{ color: '#e4e4e7', fontSize: '1rem', fontWeight: 600 }}>{(pipelineStatus.last_eval.new_score * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <p style={labelStyle}>Remplace</p>
                  <p style={{ color: pipelineStatus.last_eval.replaced ? '#34d399' : '#f87171', fontSize: '1rem', fontWeight: 600 }}>
                    {pipelineStatus.last_eval.replaced ? 'Oui' : 'Non'}
                  </p>
                </div>
              </div>
            </div>
          )}
          {trainingStats && (
            <div style={{ marginBottom: 16 }}>
              <p style={{ color: '#a1a1aa', fontSize: '0.82rem', marginBottom: 6 }}>Donnees disponibles :</p>
              <p style={{ color: '#71717a', fontSize: '0.78rem' }}>
                {trainingStats.question_logs} questions | {trainingStats.user_corrections} corrections | {trainingStats.llm_feedbacks} feedbacks LLM
              </p>
            </div>
          )}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button style={btnStyle('#5271ff')} onClick={() => doAction('retrain', () => api.post('/admin/pipeline/retrain', { epochs: 4, synthetic_examples: 6000 }))} disabled={loading.retrain}>
              {loading.retrain ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Cpu size={14} />} Lancer entrainement
            </button>
            <button style={btnStyle('#5271ff')} onClick={() => doAction('export', () => api.post('/admin/training-data/export'))} disabled={loading.export}>
              <Database size={14} /> Exporter donnees BDD
            </button>
          </div>
        </div>
      </section>

      {/* Utilisateurs */}
      <section>
        <h2 style={{ fontSize: '1.1rem', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Users size={18} color="#5271ff" /> Utilisateurs
        </h2>
        <div style={cardStyle}>
          <UsersTable />
        </div>
      </section>
    </div>
  );
}

function UsersTable() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    api.get('/admin/users').then((r) => setUsers(r.data)).catch(() => {});
  }, []);

  const toggleAdmin = async (userId) => {
    try {
      await api.patch(`/admin/users/${userId}/toggle-admin`);
      const res = await api.get('/admin/users');
      setUsers(res.data);
    } catch (err) { /* ignore */ }
  };

  return (
    <div>
      {users.map((u) => (
        <div key={u.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #1c1c22' }}>
          <div>
            <span style={{ color: '#e4e4e7', fontSize: '0.86rem' }}>{u.username}</span>
            <span style={{ color: '#52525b', fontSize: '0.75rem', marginLeft: 10 }}>{u.email}</span>
          </div>
          <button
            onClick={() => toggleAdmin(u.id)}
            style={{
              padding: '4px 10px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 500, border: 'none',
              background: u.is_admin ? '#5271ff' : '#27272a', color: u.is_admin ? 'white' : '#71717a',
            }}
          >
            {u.is_admin ? 'Admin' : 'User'}
          </button>
        </div>
      ))}
    </div>
  );
}
