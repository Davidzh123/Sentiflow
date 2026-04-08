import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Home() {
  const { user } = useAuth();

  return (
    <div>
      <h1>📊 SentiFlow</h1>
      <p style={{ color: '#aaa', fontSize: '1.1rem' }}>Analyse de sentiments Twitter en temps réel</p>

      {!user ? (
        <div style={{ marginTop: 30 }}>
          <p>Connectez-vous pour accéder au dashboard</p>
          <Link to="/login" style={{ color: '#ff4b4b', fontSize: '1.1rem' }}>🔐 Se connecter</Link>
        </div>
      ) : (
        <div style={{ marginTop: 30 }}>
          <p>Bienvenue <strong>{user.username}</strong> !</p>
          <div style={{ display: 'flex', gap: 15, marginTop: 20 }}>
            <Link to="/dashboard" className="home-link">📊 Dashboard</Link>
            <Link to="/cibles" className="home-link">🎯 Cibles</Link>
            <Link to="/alertes" className="home-link">🔔 Alertes</Link>
          </div>
        </div>
      )}
    </div>
  );
}
