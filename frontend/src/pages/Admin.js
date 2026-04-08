import React, { useState } from 'react';
import { triggerCollectAll, triggerAnalyzeAll } from '../services/api';
import { useAuth } from '../context/AuthContext';
import './Admin.css';

export default function Admin() {
  const { user } = useAuth();
  const [results, setResults] = useState([]);

  if (!user?.is_admin) {
    return <p className="info-msg">Accès réservé aux administrateurs</p>;
  }

  const runTask = async (name, fn) => {
    setResults((p) => [...p, { name, status: 'running', time: new Date().toLocaleTimeString() }]);
    try {
      const res = await fn();
      setResults((p) =>
        p.map((r) => (r.name === name && r.status === 'running' ? { ...r, status: 'done', result: res.data } : r))
      );
    } catch (err) {
      setResults((p) =>
        p.map((r) => (r.name === name && r.status === 'running' ? { ...r, status: 'error', result: err.message } : r))
      );
    }
  };

  return (
    <div>
      <h1>⚙️ Administration</h1>
      <div className="admin-actions">
        <button onClick={() => runTask('Collecte globale', triggerCollectAll)}>📥 Collecter tous les tweets</button>
        <button onClick={() => runTask('Analyse globale', triggerAnalyzeAll)}>🤖 Analyser tous les tweets</button>
      </div>

      {results.length > 0 && (
        <div className="task-results">
          <h3>Résultats</h3>
          {results.map((r, i) => (
            <div key={i} className={`task-item ${r.status}`}>
              <span>{r.time} - {r.name}</span>
              <span className="task-status">
                {r.status === 'running' ? '⏳' : r.status === 'done' ? '✅' : '❌'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
