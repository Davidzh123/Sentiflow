import React, { useState, useEffect } from 'react';
import { getTargets, getAnalysis } from '../services/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

const COLORS = ['#5271ff', '#f87171', '#38bdf8', '#fbbf24', '#34d399', '#fb923c'];

const LABELS = {
  joie: 'Joie',
  tristesse: 'Tristesse',
  colere: 'Colere',
  peur: 'Peur',
  surprise: 'Surprise',
  amour: 'Amour',
};

export default function Dashboard() {
  const [targets, setTargets] = useState([]);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [days, setDays] = useState(7);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getTargets().then((res) => {
      setTargets(res.data);
      if (res.data.length > 0) setSelectedTarget(res.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedTarget) return;
    setLoading(true);
    getAnalysis(selectedTarget, days)
      .then((res) => setAnalysis(res.data))
      .catch(() => setAnalysis(null))
      .finally(() => setLoading(false));
  }, [selectedTarget, days]);

  const chartData = analysis
    ? Object.entries(analysis.sentiment_distribution).map(([name, value]) => ({
        name: LABELS[name] || name,
        value: Math.round(value * 100),
      }))
    : [];

  return (
    <div>
      <h1 style={{ marginBottom: 4 }}>Dashboard</h1>
      <p style={{ color: '#52525b', fontSize: '0.85rem', marginBottom: 20 }}>
        Visualisation des sentiments par cible
      </p>

      {targets.length === 0 ? (
        <p className="info-msg">Aucune cible configuree. Ajoute des cibles d'abord.</p>
      ) : (
        <>
          <div className="dashboard-controls">
            <select value={selectedTarget || ''} onChange={(e) => setSelectedTarget(Number(e.target.value))}>
              {targets.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
            <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
              <option value={7}>7 jours</option>
              <option value={14}>14 jours</option>
              <option value={30}>30 jours</option>
            </select>
          </div>

          {loading ? (
            <p style={{ color: '#52525b' }}>Chargement...</p>
          ) : !analysis || analysis.total_tweets === 0 ? (
            <p className="info-msg">Pas encore de donnees pour cette cible</p>
          ) : (
            <>
              <div className="metrics">
                <div className="metric-card">
                  <span className="metric-value">{analysis.total_tweets}</span>
                  <span className="metric-label">Tweets analyses</span>
                </div>
                <div className="metric-card">
                  <span className="metric-value">{analysis.period}</span>
                  <span className="metric-label">Periode</span>
                </div>
                <div className="metric-card">
                  <span className="metric-value">{(analysis.average_confidence * 100).toFixed(0)}%</span>
                  <span className="metric-label">Confiance moyenne</span>
                </div>
              </div>

              <div className="charts">
                <div className="chart-card">
                  <h3>Repartition des sentiments</h3>
                  <ResponsiveContainer width="100%" height={280}>
                    <PieChart>
                      <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={95} label>
                        {chartData.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8 }}
                        labelStyle={{ color: '#e4e4e7' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="chart-card">
                  <h3>Sentiments (%)</h3>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={chartData}>
                      <XAxis dataKey="name" tick={{ fill: '#71717a', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#71717a' }} />
                      <Tooltip
                        contentStyle={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 8 }}
                      />
                      <Bar dataKey="value" fill="#5271ff" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
