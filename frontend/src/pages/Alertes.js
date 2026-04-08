import React, { useState, useEffect } from 'react';
import { getAlerts, createAlert, getTargets } from '../services/api';
import './Alertes.css';

const SENTIMENTS = ['joie', 'colere', 'tristesse', 'peur', 'surprise', 'amour'];

export default function Alertes() {
  const [alerts, setAlerts] = useState([]);
  const [targets, setTargets] = useState([]);
  const [form, setForm] = useState({ target_id: '', name: '', sentiment: 'joie', threshold: 0.5, is_above: true });
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    getAlerts().then((res) => setAlerts(res.data));
    getTargets().then((res) => setTargets(res.data));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await createAlert({ ...form, target_id: Number(form.target_id), threshold: Number(form.threshold) });
    getAlerts().then((res) => setAlerts(res.data));
    setShowForm(false);
  };

  return (
    <div>
      <h1>🔔 Alertes</h1>
      <button className="add-btn" onClick={() => setShowForm(!showForm)}>
        {showForm ? 'Annuler' : '+ Nouvelle alerte'}
      </button>

      {showForm && (
        <form className="alert-form" onSubmit={handleSubmit}>
          <select value={form.target_id} onChange={(e) => setForm({ ...form, target_id: e.target.value })} required>
            <option value="">Choisir une cible</option>
            {targets.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          <input placeholder="Nom de l'alerte" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <select value={form.sentiment} onChange={(e) => setForm({ ...form, sentiment: e.target.value })}>
            {SENTIMENTS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <input type="number" step="0.1" min="0" max="1" placeholder="Seuil (0-1)" value={form.threshold}
            onChange={(e) => setForm({ ...form, threshold: e.target.value })} />
          <label>
            <input type="checkbox" checked={form.is_above} onChange={(e) => setForm({ ...form, is_above: e.target.checked })} />
            Alerter si au-dessus du seuil
          </label>
          <button type="submit">Créer l'alerte</button>
        </form>
      )}

      {alerts.length === 0 ? (
        <p className="info-msg">Aucune alerte configurée</p>
      ) : (
        <div className="alerts-list">
          {alerts.map((a) => (
            <div key={a.id} className="alert-card">
              <h3>{a.name}</h3>
              <p>Sentiment: <strong>{a.sentiment}</strong></p>
              <p>Seuil: {(a.threshold * 100).toFixed(0)}% ({a.is_above ? 'au-dessus' : 'en-dessous'})</p>
              <p>Statut: {a.is_active ? '🟢 Active' : '🔴 Inactive'}</p>
              {a.last_triggered && <p>Dernière alerte: {new Date(a.last_triggered).toLocaleString()}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
