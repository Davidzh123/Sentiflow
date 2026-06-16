import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { login as apiLogin, register as apiRegister, resetPassword } from '../services/api';

export default function Login() {
  const [mode, setMode] = useState('login'); // login | register | reset
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);
  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const isRegister = mode === 'register';
  const isReset = mode === 'reset';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setInfo('');
    setLoading(true);

    try {
      if (isReset) {
        const res = await resetPassword(email, password);
        setInfo(res.data?.message || 'Mot de passe réinitialisé.');
        setMode('login'); setPassword('');
      } else if (isRegister) {
        const res = await apiRegister(email, username, password);
        loginUser(res.data.access_token, res.data.user);
        navigate('/assistant');
      } else {
        const res = await apiLogin(email, password);
        loginUser(res.data.access_token, res.data.user);
        navigate('/assistant');
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Erreur');
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: '100%',
    padding: '12px 14px',
    background: '#ffffff',
    border: '1px solid #e2e8f0',
    borderRadius: 8,
    color: '#0f172a',
    fontSize: '0.9rem',
    outline: 'none',
  };

  return (
    <div style={{ maxWidth: 380, margin: '80px auto' }}>
      <h1 style={{ marginBottom: 8 }}>{isReset ? 'Mot de passe oublié' : isRegister ? 'Creer un compte' : 'Connexion'}</h1>
      <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: 28 }}>
        {isReset ? 'Entrez votre email et un nouveau mot de passe' : isRegister ? 'Inscris-toi pour utiliser SentiFlow' : 'Connecte-toi a ton compte'}
      </p>

      {info && <p style={{ color: '#16a34a', fontSize: '0.82rem', marginBottom: 14 }}>{info}</p>}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 14 }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={inputStyle}
          />
        </div>

        {isRegister && (
          <div style={{ marginBottom: 14 }}>
            <input
              type="text"
              placeholder="Nom d'utilisateur"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={inputStyle}
            />
          </div>
        )}

        <div style={{ marginBottom: 20 }}>
          <input
            type="password"
            placeholder={isReset ? 'Nouveau mot de passe' : 'Mot de passe'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={inputStyle}
          />
        </div>

        {error && (
          <p style={{ color: '#f87171', fontSize: '0.82rem', marginBottom: 14 }}>{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px',
            background: '#5271ff',
            color: 'white',
            border: 'none',
            borderRadius: 8,
            fontWeight: 600,
            fontSize: '0.9rem',
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? 'Chargement...' : (isReset ? 'Réinitialiser' : isRegister ? "S'inscrire" : 'Se connecter')}
        </button>
      </form>

      {!isReset && !isRegister && (
        <p style={{ marginTop: 14, textAlign: 'center' }}>
          <button onClick={() => { setMode('reset'); setError(''); setInfo(''); }}
            style={{ background: 'none', border: 'none', color: '#64748b', fontSize: '0.8rem', textDecoration: 'underline' }}>
            Mot de passe oublié ?
          </button>
        </p>
      )}

      <p style={{ marginTop: 16, color: '#64748b', fontSize: '0.82rem', textAlign: 'center' }}>
        {isReset ? (
          <>
            <button onClick={() => { setMode('login'); setError(''); setInfo(''); }}
              style={{ background: 'none', border: 'none', color: '#5271ff', fontSize: '0.82rem', textDecoration: 'underline' }}>
              ← Retour à la connexion
            </button>
          </>
        ) : (
          <>
            {isRegister ? 'Deja un compte ? ' : 'Pas de compte ? '}
            <button
              onClick={() => { setMode(isRegister ? 'login' : 'register'); setError(''); setInfo(''); }}
              style={{ background: 'none', border: 'none', color: '#5271ff', fontSize: '0.82rem', textDecoration: 'underline' }}
            >
              {isRegister ? 'Se connecter' : "S'inscrire"}
            </button>
          </>
        )}
      </p>
    </div>
  );
}
