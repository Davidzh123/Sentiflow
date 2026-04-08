import React, { useState, useEffect } from 'react';
import { getTargets, getAnalysis } from '../services/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

const COLORS = ['#00C49F', '#FF4B4B', '#0088FE', '#FFBB28', '#FF8042', '#FF69B4'];
const EMOJIS = { joie: '😊', tristesse: '😢', colere: '😠', peur: '😨', surprise: '😲', amour: '❤️' };

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
        name: `${EMOJIS[name] || ''} ${name}`,
        value: Math.round(value * 100),
      }))
    : [];

  return (
    <div>
      <h1>📊 Dashboard</h1>
      {targets.length === 0 ? (
        <p className="info-msg">Aucune cible configurée. Ajoutez des cibles d'abord.</p>
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
            <p>Chargement...</p>
          ) : !analysis || analysis.total_tweets === 0 ? (
            <p className="info-msg">Pas encore de données pour cette cible</p>
          ) : (
            <>
              <div className="metrics">
                <div className="metric-card">
                  <span className="metric-value">{analysis.total_tweets}</span>
                  <span className="metric-label">Tweets analysés</span>
                </div>
                <div className="metric-card">
                  <span className="metric-value">{analysis.period}</span>
                  <span className="metric-label">Période</span>
                </div>
                <div className="metric-card">
                  <span className="metric-value">{(analysis.average_confidence * 100).toFixed(0)}%</span>
                  <span className="metric-label">Confiance moyenne</span>
                </div>
              </div>

              <div className="charts">
                <div className="chart-card">
                  <h3>Répartition des sentiments</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                        {chartData.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="chart-card">
                  <h3>Sentiments (%)</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <XAxis dataKey="name" tick={{ fill: '#aaa', fontSize: 12 }} />
                      <YAxis tick={{ fill: '#aaa' }} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#ff4b4b" radius={[4, 4, 0, 0]} />
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
