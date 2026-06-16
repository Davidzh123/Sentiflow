import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { User, Mail, Star, Download, Bell } from 'lucide-react';
import api, { getMyPlan, getInvoices, getAlerts, updateProfile } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Profile() {
  const { refreshUser } = useAuth();
  const [plan, setPlan] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [me, setMe] = useState(null);
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [saveMsg, setSaveMsg] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/auth/me').then((r) => { setMe(r.data); setNewEmail(r.data?.email || ''); }).catch(() => {});
    getMyPlan().then((r) => setPlan(r.data)).catch(() => {});
    getInvoices().then((r) => setInvoices(r.data || [])).catch(() => {});
    getAlerts().then((r) => setAlerts(r.data || [])).catch(() => {});
  }, []);

  const handleSaveProfile = async () => {
    setSaveMsg(''); setSaving(true);
    const payload = {};
    if (newEmail && newEmail !== me?.email) payload.email = newEmail;
    if (newPassword) payload.password = newPassword;
    if (Object.keys(payload).length === 0) { setSaveMsg('Aucune modification.'); setSaving(false); return; }
    try {
      const r = await updateProfile(payload);
      setMe((m) => ({ ...m, email: r.data.email }));
      setNewPassword('');
      setSaveMsg('Modifications enregistrées : ' + (r.data.changed || []).join(', '));
      await refreshUser();
      window.dispatchEvent(new Event('sentiflow:refresh-notifs'));
    } catch (e) {
      setSaveMsg(e.response?.data?.detail || 'Erreur.');
    } finally {
      setSaving(false);
    }
  };

  const downloadInvoice = async (id, number) => {
    try {
      const res = await api.get(`/billing/invoices/${id}/pdf`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url; a.download = `${number}.pdf`; a.click();
      window.URL.revokeObjectURL(url);
    } catch { /* ignore */ }
  };

  const card = { background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 20, marginBottom: 18 };
  const planLabel = plan?.current?.label || me?.plan || '-';
  const quota = plan?.quota;

  return (
    <div style={{ maxWidth: 820, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 18 }}>Mon profil</h1>

      {/* Infos */}
      <div style={card}>
        <h3 style={{ marginBottom: 14 }}>Informations</h3>
        <div style={{ display: 'grid', gap: 10 }}>
          <Row icon={<User size={16} />} label="Nom d'utilisateur" value={me?.username} />
          <Row icon={<Mail size={16} />} label="Email" value={me?.email} />
          <Row icon={<Star size={16} />} label="Rôle" value={me?.is_admin ? 'Administrateur' : 'Utilisateur'} />
        </div>
      </div>

      {/* Modifier identifiants */}
      <div style={card}>
        <h3 style={{ marginBottom: 12 }}>Modifier mes identifiants</h3>
        <div style={{ display: 'grid', gap: 10, maxWidth: 420 }}>
          <label style={{ fontSize: '0.78rem', color: '#64748b' }}>Email</label>
          <input value={newEmail} onChange={(e) => setNewEmail(e.target.value)} placeholder="nouvel email" />
          <label style={{ fontSize: '0.78rem', color: '#64748b' }}>Nouveau mot de passe</label>
          <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="laisser vide pour ne pas changer" />
          <button className="btn-primary" onClick={handleSaveProfile} disabled={saving} style={{ justifySelf: 'start' }}>
            {saving ? 'Enregistrement...' : 'Enregistrer'}
          </button>
          {saveMsg && <span style={{ fontSize: '0.8rem', color: saveMsg.startsWith('Erreur') ? '#f87171' : '#34d399' }}>{saveMsg}</span>}
        </div>
      </div>

      {/* Abonnement */}
      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Mon offre</h3>
          <Link to="/pricing" className="btn-primary" style={{ fontSize: '0.8rem' }}>Changer d'offre</Link>
        </div>
        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{
            padding: '4px 12px', borderRadius: 14, fontWeight: 700,
            background: planLabel === 'Premium' ? '#fbbf24' : planLabel === 'Standard' ? '#5271ff' : '#cbd5e1',
            color: planLabel === 'Premium' ? '#1c1917' : '#fff',
          }}>{planLabel}</span>
          {quota && (
            <span style={{ color: '#475569', fontSize: '0.85rem' }}>
              {quota.unlimited ? 'Appels IA illimités' : `${quota.remaining}/${quota.limit} appels IA restants aujourd'hui`}
            </span>
          )}
        </div>
      </div>

      {/* Factures */}
      <div style={card}>
        <h3 style={{ marginBottom: 12 }}>Mes factures</h3>
        {invoices.length === 0 ? (
          <p style={{ color: '#64748b', fontSize: '0.85rem' }}>Aucune facture pour le moment.</p>
        ) : (
          <div style={{ display: 'grid', gap: 8 }}>
            {invoices.map((inv) => (
              <div key={inv.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', background: '#f1f5f9', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.84rem' }}>
                  <strong>{inv.number}</strong>
                  <span style={{ color: '#64748b', marginLeft: 10 }}>{inv.plan} · {inv.amount_eur}€ · {inv.created_at?.slice(0, 10)}</span>
                </div>
                <button onClick={() => downloadInvoice(inv.id, inv.number)} style={{
                  display: 'inline-flex', alignItems: 'center', gap: 5, padding: '5px 10px',
                  background: 'transparent', border: '1px solid #e2e8f0', borderRadius: 6, color: '#5271ff', fontSize: '0.76rem', cursor: 'pointer',
                }}>
                  <Download size={13} /> PDF
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Alertes */}
      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Bell size={16} /> Mes alertes</h3>
          <Link to="/alertes" style={{ fontSize: '0.8rem', color: '#5271ff' }}>Gérer</Link>
        </div>
        {alerts.length === 0 ? (
          <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: 10 }}>Aucune alerte configurée.</p>
        ) : (
          <div style={{ display: 'grid', gap: 6, marginTop: 10 }}>
            {alerts.map((a) => (
              <div key={a.id} style={{ fontSize: '0.82rem', color: '#475569', padding: '6px 10px', background: '#f1f5f9', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                {a.name} — {a.sentiment} {a.is_above ? '≥' : '≤'} {a.threshold}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ icon, label, value }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ color: '#5271ff' }}>{icon}</span>
      <span style={{ color: '#64748b', fontSize: '0.82rem', width: 150 }}>{label}</span>
      <span style={{ color: '#1e293b', fontSize: '0.88rem' }}>{value || '-'}</span>
    </div>
  );
}
