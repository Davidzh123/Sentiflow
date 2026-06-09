import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { deleteGeneratedDashboard, getGeneratedDashboards } from '../services/api';
import './GeneratedDashboards.css';

function formatDate(value) {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('fr-FR');
  } catch (_err) {
    return String(value);
  }
}

export default function GeneratedDashboards() {
  const [dashboards, setDashboards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDashboards = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await getGeneratedDashboards();
      setDashboards(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Impossible de charger les dashboards générés.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboards();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm('Supprimer ce dashboard généré ?')) return;

    try {
      await deleteGeneratedDashboard(id);
      setDashboards((current) => current.filter((dashboard) => dashboard.id !== id));
    } catch (err) {
      setError(err.response?.data?.detail || 'Suppression impossible.');
    }
  };

  return (
    <div className="generated-dashboard-list-page">
      <div className="generated-dashboard-list-header">
        <div>
          <h1>📈 Dashboards générés</h1>
          <p>
            Retrouve ici les dashboards créés automatiquement par l'assistant LLM.
          </p>
        </div>
        <Link to="/assistant" className="generated-primary-link">
          Créer via le LLM
        </Link>
      </div>

      {error && <div className="generated-error-message">{error}</div>}

      {loading ? (
        <p className="generated-info-message">Chargement...</p>
      ) : dashboards.length === 0 ? (
        <div className="generated-empty-state">
          <h2>Aucun dashboard généré</h2>
          <p>
            Va dans l'assistant LLM et demande par exemple :
            <br />
            <strong>compare france et minecraft puis génère un dashboard</strong>
          </p>
          <Link to="/assistant" className="generated-primary-link">
            Ouvrir l'assistant
          </Link>
        </div>
      ) : (
        <div className="generated-dashboard-grid">
          {dashboards.map((dashboard) => (
            <article className="generated-dashboard-card" key={dashboard.id}>
              <div>
                <h2>{dashboard.title}</h2>
                <p className="generated-question">{dashboard.question}</p>
              </div>

              <div className="generated-card-meta">
                <span>Créé le {formatDate(dashboard.created_at)}</span>
                <span>{dashboard.target_ids?.length || 0} cible(s)</span>
              </div>

              <div className="dashboard-list-actions">
                <Link to={`/dashboards/generated/${dashboard.id}`} className="generated-secondary-link">
                  Voir le dashboard
                </Link>
                <button type="button" onClick={() => handleDelete(dashboard.id)}>
                  Supprimer
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
