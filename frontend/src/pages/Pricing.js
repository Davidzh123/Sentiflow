import React, { useEffect, useState } from 'react';
import { Check, X, Zap } from 'lucide-react';
import { getMyPlan, subscribePlan } from '../services/api';
import { useAuth } from '../context/AuthContext';

const ORDER = ['free', 'standard', 'premium'];

export default function Pricing() {
  const { refreshUser } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [checkout, setCheckout] = useState(null);
  const [cardName, setCardName] = useState('');
  const [cardNum, setCardNum] = useState('');
  const [paying, setPaying] = useState(false);
  const [done, setDone] = useState('');

  const reload = () => getMyPlan().then((res) => setData(res.data)).catch((e) => setError(e.response?.data?.detail || 'Erreur.'));
  useEffect(() => { reload(); }, []);

  if (error) return <div className="card" style={{ color: '#f87171' }}>{error}</div>;
  if (!data) return <p style={{ color: '#64748b' }}>Chargement...</p>;

  const { current, quota, catalog } = data;
  const currentPlan = current?.plan;

  const startCheckout = (key) => {
    setDone('');
    if (key === 'free') { pay('free'); return; }
    setCheckout(key); setCardName(''); setCardNum('');
  };

  const pay = async (key) => {
    setPaying(true);
    try {
      await subscribePlan(key, cardName);
      setCheckout(null);
      setDone(`Offre ${catalog[key].label} activée !`);
      await reload();
      await refreshUser();
      window.dispatchEvent(new Event('sentiflow:refresh-notifs'));
    } catch (e) {
      setError(e.response?.data?.detail || 'Paiement impossible.');
    } finally {
      setPaying(false);
    }
  };

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h1 style={{ marginBottom: 8 }}>Offres SentiFlow</h1>
        <p style={{ color: '#64748b' }}>
          Votre offre actuelle : <strong style={{ color: '#5271ff' }}>{catalog[currentPlan]?.label}</strong>
          {quota && !quota.unlimited && (
            <> — {quota.remaining}/{quota.limit} appels IA restants aujourd'hui</>
          )}
          {quota && quota.unlimited && <> — appels IA illimités</>}
        </p>
        {done && <p style={{ color: '#34d399', marginTop: 8 }}>{done}</p>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 18 }}>
        {ORDER.map((key) => {
          const plan = catalog[key];
          if (!plan) return null;
          const isCurrent = key === currentPlan;
          const highlight = key === 'premium';
          return (
            <div
              key={key}
              className="card"
              style={{
                border: isCurrent ? '2px solid #5271ff' : highlight ? '1px solid #5271ff55' : '1px solid #e2e8f0',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              {isCurrent && (
                <span style={{
                  position: 'absolute', top: -11, left: '50%', transform: 'translateX(-50%)',
                  background: '#5271ff', color: 'white', fontSize: '0.7rem', padding: '2px 10px', borderRadius: 12,
                }}>Offre actuelle</span>
              )}
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {highlight && <Zap size={16} color="#fbbf24" />} {plan.label}
              </h3>
              <div style={{ margin: '12px 0' }}>
                <span style={{ fontSize: '1.8rem', fontWeight: 700 }}>{plan.price_eur}€</span>
                <span style={{ color: '#64748b', fontSize: '0.85rem' }}> / mois</span>
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, flex: 1 }}>
                {plan.features.map((f, i) => (
                  <li key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 8, fontSize: '0.85rem' }}>
                    <Check size={15} color="#34d399" style={{ flexShrink: 0, marginTop: 2 }} /> {f}
                  </li>
                ))}
                {plan.limitations.map((f, i) => (
                  <li key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 8, fontSize: '0.85rem', color: '#64748b' }}>
                    <X size={15} color="#f87171" style={{ flexShrink: 0, marginTop: 2 }} /> {f}
                  </li>
                ))}
              </ul>
              <div style={{ marginTop: 16 }}>
                {isCurrent ? (
                  <button className="btn-primary" disabled style={{ width: '100%', opacity: 0.6 }}>
                    Offre active
                  </button>
                ) : (
                  <button className="btn-primary" style={{ width: '100%' }} onClick={() => startCheckout(key)}>
                    {key === 'free' ? 'Passer en Free' : `Choisir — ${plan.price_eur}€/mois`}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {checkout && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 100,
        }} onClick={() => setCheckout(null)}>
          <div className="card" style={{ width: 380, maxWidth: '90%' }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginBottom: 4 }}>Paiement — {catalog[checkout].label}</h3>
            <p style={{ color: '#64748b', fontSize: '0.8rem', marginBottom: 14 }}>
              {catalog[checkout].price_eur}€ / mois · paiement sécurisé (démo)
            </p>
            <div style={{ display: 'grid', gap: 10 }}>
              <input placeholder="Nom sur la carte" value={cardName} onChange={(e) => setCardName(e.target.value)} />
              <input placeholder="N° de carte (4242 4242 4242 4242)" value={cardNum} onChange={(e) => setCardNum(e.target.value)} />
              <div style={{ display: 'flex', gap: 10 }}>
                <input placeholder="MM/AA" style={{ flex: 1 }} />
                <input placeholder="CVC" style={{ flex: 1 }} />
              </div>
              <button className="btn-primary" disabled={paying} onClick={() => pay(checkout)}>
                {paying ? 'Paiement...' : `Payer ${catalog[checkout].price_eur}€`}
              </button>
              <button onClick={() => setCheckout(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '0.8rem' }}>
                Annuler
              </button>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.7rem', marginTop: 10 }}>
              Environnement de démonstration — aucune carte réelle n'est débitée.
            </p>
          </div>
        </div>
      )}

      <p style={{ color: '#64748b', fontSize: '0.8rem', textAlign: 'center', marginTop: 24 }}>
        Une facture est générée automatiquement après paiement (téléchargeable dans votre profil).
      </p>
    </div>
  );
}
