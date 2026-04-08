import React, { useState, useEffect } from 'react';
import { getTargets, createTarget, deleteTarget, collectTweets, analyzeTweets, getTweets } from '../services/api';
import { Trash2 } from 'lucide-react';
import './Cibles.css';

const EMOJIS = { joie: '😊', tristesse: '😢', colere: '😠', peur: '😨', surprise: '😲', amour: '❤️' };

export default function Cibles() {
  const [targets, setTargets] = useState([]);
  const [name, setName] = useState('');
  const [type, setType] = useState('hashtag');
  const [loading, setLoading] = useState({});
  const [tweets, setTweets] = useState({});
  const [msg, setMsg] = useState({});

  const loadTargets = () => {
    getTargets().then((res) => setTargets(res.data));
  };

  useEffect(() => { loadTargets(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!name) return;
    await createTarget(name, type);
    setName('');
    loadTargets();
  };

  const handleDelete = async (id) => {
    await deleteTarget(id);
    loadTargets();
  };

  const handleCollect = async (id) => {
    setLoading((p) => ({ ...p, [`c_${id}`]: true }));
    setMsg((p) => ({ ...p, [id]: null }));
    try {
      const res = await collectTweets(id);
      setMsg((p) => ({ ...p, [id]: { type: 'success', text: `${res.data.saved} tweets collectés` } }));
      loadTweets(id);
    } catch (err) {
      setMsg((p) => ({ ...p, [id]: { type: 'error', text: err.response?.data?.detail || 'Erreur collecte' } }));
    }
    setLoading((p) => ({ ...p, [`c_${id}`]: false }));
  };

  const handleAnalyze = async (id) => {
    setLoading((p) => ({ ...p, [`a_${id}`]: true }));
    setMsg((p) => ({ ...p, [id]: null }));
    try {
      const res = await analyzeTweets(id);
      setMsg((p) => ({ ...p, [id]: { type: 'success', text: `${res.data.analyzed} tweets analysés` } }));
      loadTweets(id);
    } catch (err) {
      setMsg((p) => ({ ...p, [id]: { type: 'error', text: err.response?.data?.detail || 'Erreur analyse' } }));
    }
    setLoading((p) => ({ ...p, [`a_${id}`]: false }));
  };

  const loadTweets = (id) => {
    getTweets(id, 100).then((res) => setTweets((p) => ({ ...p, [id]: res.data })));
  };

  useEffect(() => {
    targets.forEach((t) => loadTweets(t.id));
    // eslint-disable-next-line
  }, [targets]);

  return (
    <div>
      <h1>🎯 Gérer les cibles</h1>

      <form className="add-form" onSubmit={handleAdd}>
        <input placeholder="#MachineLearning ou @elonmusk" value={name} onChange={(e) => setName(e.target.value)} />
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="hashtag">Hashtag</option>
          <option value="account">Compte</option>
        </select>
        <button type="submit">Ajouter</button>
      </form>

      {targets.length === 0 ? (
        <p className="info-msg">Aucune cible. Ajoutez un hashtag ou un compte ci-dessus.</p>
      ) : (
        targets.map((target) => {
          const tw = tweets[target.id] || [];
          const analyzed = tw.filter((t) => t.sentiment);
          const sentimentCounts = {};
          analyzed.forEach((t) => {
            sentimentCounts[t.sentiment] = (sentimentCounts[t.sentiment] || 0) + 1;
          });

          return (
            <div key={target.id} className="target-card">
              <div className="target-header">
                <h3>{target.target_type === 'hashtag' ? '#️⃣' : '👤'} {target.name}</h3>
                <button className="delete-btn" onClick={() => handleDelete(target.id)}>
                  <Trash2 size={16} />
                </button>
              </div>

              <div className="target-actions">
                <button onClick={() => handleCollect(target.id)} disabled={loading[`c_${target.id}`]}>
                  {loading[`c_${target.id}`] ? '⏳' : '📥'} Collecter
                </button>
                <button className="primary" onClick={() => handleAnalyze(target.id)} disabled={loading[`a_${target.id}`]}>
                  {loading[`a_${target.id}`] ? '⏳' : '🤖'} Analyser
                </button>
              </div>

              {msg[target.id] && (
                <div className={`msg ${msg[target.id].type}`}>{msg[target.id].text}</div>
              )}

              <div className="target-stats">
                📈 {tw.length} tweets | ✅ {analyzed.length} analysés | ⏳ {tw.length - analyzed.length} en attente
              </div>

              {Object.keys(sentimentCounts).length > 0 && (
                <div className="sentiment-pills">
                  {Object.entries(sentimentCounts)
                    .sort((a, b) => b[1] - a[1])
                    .map(([sent, count]) => (
                      <span key={sent} className="pill">
                        {EMOJIS[sent] || '❓'} {sent} {Math.round((count / analyzed.length) * 100)}%
                      </span>
                    ))}
                </div>
              )}

              {tw.length > 0 && (
                <details className="tweets-list">
                  <summary>📝 Voir les tweets ({tw.length})</summary>
                  <table>
                    <thead>
                      <tr><th>Sentiment</th><th>Confiance</th><th>Tweet</th><th>Auteur</th></tr>
                    </thead>
                    <tbody>
                      {tw.slice(0, 20).map((t, i) => (
                        <tr key={i}>
                          <td>{t.sentiment ? `${EMOJIS[t.sentiment] || '❓'} ${t.sentiment}` : '⏳'}</td>
                          <td>{t.confidence ? `${(t.confidence * 100).toFixed(0)}%` : '-'}</td>
                          <td className="tweet-text">{t.text?.slice(0, 120)}</td>
                          <td>@{t.author_username || '?'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </details>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}
