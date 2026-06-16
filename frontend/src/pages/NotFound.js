import React from 'react';
import { Link } from 'react-router-dom';
import { Compass } from 'lucide-react';

export default function NotFound() {
  return (
    <div style={{ maxWidth: 520, margin: '60px auto', textAlign: 'center' }}>
      <Compass size={48} color="#5271ff" style={{ marginBottom: 16 }} />
      <h1 style={{ fontSize: '3rem', marginBottom: 4 }}>404</h1>
      <h2 style={{ marginBottom: 12 }}>Page introuvable</h2>
      <p style={{ color: '#475569', marginBottom: 24 }}>
        La page que vous cherchez n'existe pas ou a été déplacée.
      </p>
      <Link to="/" className="btn-primary">Retour à l'accueil</Link>
    </div>
  );
}
