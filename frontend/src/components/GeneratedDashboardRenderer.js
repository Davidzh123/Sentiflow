import React, { useEffect, useMemo, useState } from 'react';
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';
import api from '../services/api';
import './GeneratedDashboardRenderer.css';

const SENTIMENTS = ['joie', 'amour', 'surprise', 'neutre', 'peur', 'tristesse', 'colere'];
const SENTIMENT_LABELS = {
  joie: 'Joie',
  amour: 'Amour',
  colere: 'Colère',
  tristesse: 'Tristesse',
  peur: 'Peur',
  surprise: 'Surprise',
  neutre: 'Neutre',
};
const SENTIMENT_COLORS = {
  joie: '#22c55e',
  amour: '#ec4899',
  colere: '#ef4444',
  tristesse: '#3b82f6',
  peur: '#a855f7',
  surprise: '#f59e0b',
  neutre: '#94a3b8',
};
const SERIES_COLORS = ['#5271ff', '#22c55e', '#f59e0b', '#ec4899', '#a855f7', '#14b8a6', '#ef4444'];
const WORD_CLOUD_COLORS = ['#8ea2ff', '#22c55e', '#f59e0b', '#ec4899', '#38bdf8', '#a855f7', '#f87171'];

function percent(value) {
  const numeric = Number(value || 0);
  if (numeric <= 1) return `${Math.round(numeric * 100)}%`;
  return `${Math.round(numeric)}%`;
}

function score(value) {
  const numeric = Number(value || 0);
  return numeric > 0 ? `+${numeric.toFixed(2)}` : numeric.toFixed(2);
}

function formatDate(value, withTime = true) {
  if (!value) return '-';
  try {
    const options = withTime
      ? { dateStyle: 'medium', timeStyle: 'short' }
      : { dateStyle: 'medium' };
    return new Date(value).toLocaleString('fr-FR', options);
  } catch (_err) {
    return String(value);
  }
}

function getWidget(config, type) {
  return config?.widgets?.find((widget) => widget.type === type);
}

function getWidgetData(config, type, fallback) {
  return getWidget(config, type)?.data ?? fallback;
}

function countsToChartData(item) {
  const counts = item?.counts || {};
  const distribution = item?.distribution || {};
  return SENTIMENTS.map((sentiment) => ({
    sentiment,
    name: SENTIMENT_LABELS[sentiment] || sentiment,
    value: Number(counts[sentiment] ?? 0),
    percent: Number(distribution[sentiment] ?? 0),
  })).filter((row) => row.value > 0 || row.percent > 0);
}

function buildTargetMetrics(distributionWidget, insightWidget) {
  const distributionTargets = distributionWidget?.data || [];
  const insights = insightWidget?.data || [];
  const insightByTarget = Object.fromEntries(
    insights.map((item) => [String(item.target_id || item.target_name), item])
  );

  return distributionTargets.map((target) => {
    const counts = target.counts || {};
    const distribution = target.distribution || {};
    const total = Object.values(counts).reduce((sum, value) => sum + Number(value || 0), 0);
    const dominant = SENTIMENTS.reduce(
      (best, sentiment) => Number(distribution[sentiment] || 0) > Number(distribution[best] || 0) ? sentiment : best,
      SENTIMENTS[0]
    );
    const insight = insightByTarget[String(target.target_id)] || insightByTarget[String(target.target_name)] || {};

    return {
      targetId: target.target_id,
      targetName: target.target_name,
      total,
      dominant,
      dominantPercent: Number(distribution[dominant] || 0),
      netScore: insight.net_sentiment_score,
      confidence: insight.average_confidence,
    };
  });
}

function buildComparisonData(comparisonWidget, distributionWidget) {
  const dataSource = comparisonWidget?.data || distributionWidget?.data || [];
  return dataSource.map((target) => {
    const distribution = target.sentiment_distribution || target.distribution || {};
    const row = {
      targetName: target.target_name,
      total_tweets: target.total_tweets || Object.values(target.counts || {}).reduce((sum, value) => sum + Number(value || 0), 0),
      dominant_sentiment: target.dominant_sentiment,
      net_sentiment_score: Number(target.net_sentiment_score || 0),
    };

    SENTIMENTS.forEach((sentiment) => {
      row[sentiment] = Math.round(Number(distribution[sentiment] || 0) * 100);
    });
    return row;
  });
}

function buildTimelineData(timelineWidget) {
  const raw = timelineWidget?.data || {};
  const rowsByDate = {};
  const targetNames = Object.keys(raw || {});

  targetNames.forEach((targetName) => {
    (raw[targetName] || []).forEach((point) => {
      const date = point.date;
      if (!rowsByDate[date]) rowsByDate[date] = { date, totalVolume: 0 };
      rowsByDate[date][targetName] = Number(point.net_sentiment_score ?? 0);
      rowsByDate[date][`${targetName}Volume`] = Number(point.total || 0);
      rowsByDate[date].totalVolume += Number(point.total || 0);
    });
  });

  return {
    targetNames,
    rows: Object.values(rowsByDate).sort((a, b) => String(a.date).localeCompare(String(b.date))),
  };
}

function buildSentimentBars(distributionWidget) {
  return (distributionWidget?.data || []).map((target) => {
    const counts = target.counts || {};
    const row = { targetName: target.target_name };
    SENTIMENTS.forEach((sentiment) => {
      row[sentiment] = Number(counts[sentiment] || 0);
    });
    return row;
  });
}

function buildKeywordRows(keywordWidget) {
  const rows = [];
  (keywordWidget?.data || []).forEach((target) => {
    (target.keywords || []).forEach((keyword) => {
      const sentimentCounts = keyword.sentiment_counts || {};
      const dominantSentiment = keyword.dominant_sentiment
        || Object.entries(sentimentCounts).sort((a, b) => Number(b[1] || 0) - Number(a[1] || 0))[0]?.[0]
        || null;
      rows.push({
        targetId: target.target_id,
        targetName: target.target_name,
        term: keyword.term,
        count: Number(keyword.count || 0),
        docCount: Number(keyword.doc_count || keyword.count || 0),
        score: Number(keyword.score || keyword.count || 0),
        sentimentCounts,
        dominantSentiment,
        label: `${target.target_name} - ${keyword.term}`,
      });
    });
  });
  return rows.sort((a, b) => b.score - a.score || b.count - a.count).slice(0, 24);
}

function buildWordCloudRows(keywordWidget) {
  const rows = buildKeywordRows(keywordWidget).slice(0, 36);
  if (!rows.length) return [];

  const maxScore = Math.max(...rows.map((row) => row.score || row.count || 1), 1);
  const minScore = Math.min(...rows.map((row) => row.score || row.count || 1), maxScore);
  const spread = Math.max(maxScore - minScore, 1);

  return rows.map((row, index) => {
    const normalized = ((row.score || row.count || 1) - minScore) / spread;
    return {
      ...row,
      size: Math.round(14 + normalized * 24),
      color: SENTIMENT_COLORS[row.dominantSentiment] || WORD_CLOUD_COLORS[index % WORD_CLOUD_COLORS.length],
      weight: Math.round(500 + normalized * 350),
    };
  });
}

function buildKeywordSentimentRows(keywordWidget) {
  return buildKeywordRows(keywordWidget)
    .filter((row) => Object.values(row.sentimentCounts || {}).some((value) => Number(value || 0) > 0))
    .slice(0, 12);
}

function buildQualityMapData(metrics) {
  return metrics
    .filter((item) => Number(item.total || 0) > 0)
    .map((item) => ({
      targetName: item.targetName,
      volume: Number(item.total || 0),
      netScore: Number(item.netScore || 0),
      confidence: Math.round(Number(item.confidence || 0) * 100),
      dominant: item.dominant,
      dominantPercent: Number(item.dominantPercent || 0),
    }));
}

function DashboardMetrics({ metrics, summary }) {
  const totalTweets = summary?.tweet_count || metrics.reduce((sum, item) => sum + item.total, 0);
  const targetCount = metrics.length;
  const mostActive = metrics.reduce((best, item) => item.total > (best?.total || 0) ? item : best, null);
  const avgNetScore = metrics.length
    ? metrics.reduce((sum, item) => sum + Number(item.netScore || 0), 0) / metrics.length
    : 0;
  const avgConfidence = metrics.length
    ? metrics.reduce((sum, item) => sum + Number(item.confidence || 0), 0) / metrics.length
    : 0;

  return (
    <div className="generated-dashboard-metrics">
      <div className="generated-metric-card">
        <span className="generated-metric-value">{totalTweets}</span>
        <span className="generated-metric-label">Tweets dans la période</span>
      </div>
      <div className="generated-metric-card">
        <span className="generated-metric-value">{targetCount}</span>
        <span className="generated-metric-label">Cibles analysées</span>
      </div>
      <div className="generated-metric-card">
        <span className="generated-metric-value">{score(avgNetScore)}</span>
        <span className="generated-metric-label">Score émotionnel moyen</span>
      </div>
      <div className="generated-metric-card">
        <span className="generated-metric-value">{percent(avgConfidence)}</span>
        <span className="generated-metric-label">Confiance moyenne</span>
      </div>
      <div className="generated-metric-card generated-wide-metric">
        <span className="generated-metric-value">{mostActive?.targetName || '-'}</span>
        <span className="generated-metric-label">Cible la plus active</span>
      </div>
    </div>
  );
}

function CollectionSummary({ widget, dashboardConfig }) {
  const data = widget?.data || dashboardConfig?.period;
  if (!data) return null;

  return (
    <section className="generated-period-band">
      <div>
        <span>Période</span>
        <strong>{data.period_days || data.days || '-'} jour(s)</strong>
      </div>
      <div>
        <span>Début</span>
        <strong>{formatDate(data.from)}</strong>
      </div>
      <div>
        <span>Fin</span>
        <strong>{formatDate(data.to)}</strong>
      </div>
      <div>
        <span>Base de date</span>
        <strong>{data.date_basis || 'date du tweet / récupération'}</strong>
      </div>
    </section>
  );
}

function SentimentDonutWidget({ widget }) {
  if (!widget?.data?.length) return null;

  return (
    <section className="generated-widget-card">
      <div className="generated-widget-header">
        <h2>{widget.title || 'Répartition des sentiments'}</h2>
        <p>Lecture par cible avec volume réel et proportion de chaque émotion.</p>
      </div>

      <div className="generated-pie-grid">
        {widget.data.map((target) => {
          const chartData = countsToChartData(target);
          return (
            <div className="generated-pie-card" key={target.target_id || target.target_name}>
              <div className="generated-pie-heading">
                <h3>{target.target_name}</h3>
                <span>{chartData.reduce((sum, row) => sum + row.value, 0)} tweets</span>
              </div>
              {chartData.length === 0 ? (
                <p className="generated-empty">Pas de données.</p>
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={230}>
                    <PieChart>
                      <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={58} outerRadius={84} paddingAngle={3}>
                        {chartData.map((entry) => (
                          <Cell key={entry.sentiment} fill={SENTIMENT_COLORS[entry.sentiment]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value, name, item) => [`${value} tweets (${percent(item.payload.percent)})`, name]} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="generated-sentiment-list">
                    {chartData.map((row) => (
                      <div className="generated-sentiment-row" key={row.sentiment}>
                        <span className="generated-dot" style={{ background: SENTIMENT_COLORS[row.sentiment] }} />
                        <span>{row.name}</span>
                        <strong>{row.value} ({percent(row.percent)})</strong>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}

function SentimentStackWidget({ distributionWidget }) {
  const rows = buildSentimentBars(distributionWidget);
  if (!rows.length) return null;

  return (
    <section className="generated-widget-card">
      <div className="generated-widget-header">
        <h2>Volume par émotion</h2>
        <p>Barres empilées : utile pour comparer le poids réel de chaque tonalité.</p>
      </div>
      <ResponsiveContainer width="100%" height={340}>
        <BarChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="targetName" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" allowDecimals={false} />
          <Tooltip />
          <Legend formatter={(value) => SENTIMENT_LABELS[value] || value} />
          {SENTIMENTS.map((sentiment) => (
            <Bar key={sentiment} dataKey={sentiment} stackId="sentiments" fill={SENTIMENT_COLORS[sentiment]} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

function TargetComparisonWidget({ comparisonWidget, distributionWidget }) {
  const chartData = buildComparisonData(comparisonWidget, distributionWidget);
  if (!chartData.length) return null;

  return (
    <section className="generated-widget-card">
      <div className="generated-widget-header">
        <h2>{comparisonWidget?.title || 'Comparaison des cibles'}</h2>
        <p>Score émotionnel et volume de tweets, pour éviter de comparer seulement des pourcentages.</p>
      </div>

      <ResponsiveContainer width="100%" height={360}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="targetName" stroke="#94a3b8" />
          <YAxis yAxisId="left" stroke="#94a3b8" allowDecimals={false} />
          <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" domain={[-1, 1]} />
          <Tooltip />
          <Legend />
          <Bar yAxisId="left" dataKey="total_tweets" name="Tweets" fill="#334155" radius={[8, 8, 0, 0]} />
          <Line yAxisId="right" type="monotone" dataKey="net_sentiment_score" name="Score émotionnel" stroke="#5271ff" strokeWidth={3} dot={{ r: 5 }} />
          <ReferenceLine yAxisId="right" y={0} stroke="#64748b" strokeDasharray="4 4" />
        </ComposedChart>
      </ResponsiveContainer>
    </section>
  );
}

function TargetQualityMapWidget({ metrics }) {
  const rows = buildQualityMapData(metrics);
  if (!rows.length) return null;

  return (
    <section className="generated-widget-card">
      <div className="generated-widget-header">
        <h2>Carte volume / confiance</h2>
        <p>Chaque point croise le volume de tweets, le score émotionnel et la confiance moyenne du modèle.</p>
      </div>
      <ResponsiveContainer width="100%" height={340}>
        <ScatterChart margin={{ top: 12, right: 26, bottom: 22, left: 6 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis
            type="number"
            dataKey="volume"
            name="Volume"
            stroke="#94a3b8"
            allowDecimals={false}
          />
          <YAxis
            type="number"
            dataKey="netScore"
            name="Score émotionnel"
            stroke="#94a3b8"
            domain={[-1, 1]}
          />
          <ZAxis type="number" dataKey="confidence" range={[90, 420]} name="Confiance" unit="%" />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            formatter={(value, name) => {
              if (name === 'Score émotionnel') return [Number(value).toFixed(2), name];
              return [value, name];
            }}
            labelFormatter={(_, payload) => payload?.[0]?.payload?.targetName || ''}
          />
          <ReferenceLine y={0} stroke="#64748b" strokeDasharray="4 4" />
          <Scatter data={rows} name="Cibles">
            {rows.map((entry) => (
              <Cell key={entry.targetName} fill={SENTIMENT_COLORS[entry.dominant] || '#5271ff'} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <div className="generated-quality-legend">
        {rows.map((row) => (
          <span key={row.targetName}>
            <i style={{ background: SENTIMENT_COLORS[row.dominant] || '#5271ff' }} />
            {row.targetName} · {SENTIMENT_LABELS[row.dominant] || row.dominant || 'inconnu'} ({percent(row.dominantPercent)})
          </span>
        ))}
      </div>
    </section>
  );
}

function SentimentTimelineWidget({ widget }) {
  const timeline = buildTimelineData(widget);
  if (!timeline.rows.length) return null;

  return (
    <section className="generated-widget-card">
      <div className="generated-widget-header">
        <h2>{widget?.title || 'Évolution temporelle'}</h2>
        <p>Score émotionnel jour par jour, basé sur la date du tweet ou la date de récupération si nécessaire.</p>
      </div>
      <ResponsiveContainer width="100%" height={360}>
        <ComposedChart data={timeline.rows} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
          <defs>
            <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#5271ff" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#5271ff" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" stroke="#94a3b8" />
          <YAxis yAxisId="left" stroke="#94a3b8" domain={[-1, 1]} />
          <YAxis yAxisId="right" orientation="right" stroke="#64748b" allowDecimals={false} />
          <Tooltip />
          <Legend />
          <Area yAxisId="right" type="monotone" dataKey="totalVolume" name="Volume total" fill="url(#volumeGradient)" stroke="#334155" />
          <ReferenceLine yAxisId="left" y={0} stroke="#64748b" strokeDasharray="4 4" />
          {timeline.targetNames.map((targetName, index) => (
            <Line
              yAxisId="left"
              key={targetName}
              type="monotone"
              dataKey={targetName}
              stroke={SERIES_COLORS[index % SERIES_COLORS.length]}
              strokeWidth={3}
              dot={{ r: 4 }}
              connectNulls
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </section>
  );
}

function KeywordWordCloudWidget({ widget }) {
  const words = buildWordCloudRows(widget);
  if (!words.length) return null;

  return (
    <section className="generated-widget-card generated-word-cloud-card">
      <div className="generated-widget-header">
        <h2>Nuage de mots pertinents</h2>
        <p>Termes pondérés par fréquence, nombre de tweets concernés et signal émotionnel. Le hashtag cible est exclu.</p>
      </div>
      <div className="generated-word-cloud" aria-label="Nuage de mots clés">
        {words.map((word) => (
          <span
            key={`${word.targetName}-${word.term}`}
            title={`${word.targetName} · ${word.count} occurrences · ${SENTIMENT_LABELS[word.dominantSentiment] || word.dominantSentiment || 'sentiment mixte'}`}
            style={{
              color: word.color,
              fontSize: `${word.size}px`,
              fontWeight: word.weight,
            }}
          >
            {word.term}
          </span>
        ))}
      </div>
    </section>
  );
}

function KeywordTopicsWidget({ widget }) {
  const rows = buildKeywordRows(widget);
  if (!rows.length) return null;

  return (
    <section className="generated-widget-card">
      <div className="generated-widget-header">
        <h2>{widget.title || 'Mots et sujets récurrents'}</h2>
        <p>Mots les plus fréquents dans les tweets collectés, après nettoyage simple.</p>
      </div>
      <ResponsiveContainer width="100%" height={Math.max(280, rows.length * 28)}>
        <BarChart data={rows} layout="vertical" margin={{ top: 10, right: 20, left: 120, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis type="number" stroke="#94a3b8" allowDecimals={false} />
          <YAxis type="category" dataKey="label" stroke="#94a3b8" width={130} />
          <Tooltip formatter={(value, name) => [name === 'score' ? Number(value).toFixed(2) : value, name === 'score' ? 'Score de pertinence' : 'Fréquence']} />
          <Bar dataKey="score" fill="#5271ff" radius={[0, 8, 8, 0]}>
            {rows.map((row, index) => (
              <Cell key={`${row.targetName}-${row.term}`} fill={SENTIMENT_COLORS[row.dominantSentiment] || WORD_CLOUD_COLORS[index % WORD_CLOUD_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

function KeywordSentimentMatrixWidget({ widget }) {
  const rows = buildKeywordSentimentRows(widget);
  if (!rows.length) return null;

  const maxValue = Math.max(
    ...rows.flatMap((row) => SENTIMENTS.map((sentiment) => Number(row.sentimentCounts?.[sentiment] || 0))),
    1
  );

  return (
    <section className="generated-widget-card">
      <div className="generated-widget-header">
        <h2>Matrice mots / émotions</h2>
        <p>Les mots importants sont croisés avec les émotions qu'ils portent le plus souvent.</p>
      </div>
      <div className="generated-keyword-matrix">
        <div className="generated-keyword-matrix-head">
          <span>Mot</span>
          {SENTIMENTS.map((sentiment) => (
            <span key={sentiment}>{SENTIMENT_LABELS[sentiment]}</span>
          ))}
        </div>
        {rows.map((row) => (
          <div className="generated-keyword-matrix-row" key={`${row.targetName}-${row.term}`}>
            <strong>{row.term}<small>{row.targetName}</small></strong>
            {SENTIMENTS.map((sentiment) => {
              const value = Number(row.sentimentCounts?.[sentiment] || 0);
              const opacity = value ? 0.18 + (value / maxValue) * 0.72 : 0.06;
              return (
                <span
                  key={sentiment}
                  className="generated-keyword-cell"
                  style={{ background: SENTIMENT_COLORS[sentiment], opacity }}
                  title={`${row.term} · ${SENTIMENT_LABELS[sentiment]} : ${value}`}
                >
                  {value || ''}
                </span>
              );
            })}
          </div>
        ))}
      </div>
    </section>
  );
}

function InsightSummaryWidget({ widget }) {
  if (!widget?.data?.length) return null;

  return (
    <section className="generated-insight-grid">
      {widget.data.map((item) => (
        <article className="generated-insight-card" key={item.target_id || item.target_name}>
          <div>
            <h3>{item.target_name}</h3>
            <p>{item.net_sentiment_label || 'Lecture non disponible'}</p>
          </div>
          <div className="generated-insight-score">{score(item.net_sentiment_score)}</div>
          <div className="generated-insight-stats">
            <span>Positif <strong>{percent(item.positive_ratio)}</strong></span>
            <span>Négatif <strong>{percent(item.negative_ratio)}</strong></span>
            <span>Confiance <strong>{percent(item.average_confidence)}</strong></span>
          </div>
          {item.trend && (
            <p className="generated-insight-note">
              Tendance : {item.trend.label || item.trend.direction || 'stable'}
              {typeof item.trend.score_delta === 'number' ? ` (${score(item.trend.score_delta)})` : ''}
            </p>
          )}
        </article>
      ))}
    </section>
  );
}

function SentimentBadge({ sentiment }) {
  return (
    <span className="generated-sentiment-badge" style={{ borderColor: SENTIMENT_COLORS[sentiment] || '#64748b', color: SENTIMENT_COLORS[sentiment] || '#cbd5e1' }}>
      {SENTIMENT_LABELS[sentiment] || sentiment || 'Inconnu'}
    </span>
  );
}

function FeedbackButton({ tweet, disabled, onFeedback }) {
  return (
    <button
      type="button"
      className="generated-feedback-button"
      disabled={disabled}
      onClick={() => onFeedback(tweet)}
      title="Signaler que le sentiment prédit est incorrect"
    >
      Pas satisfait
    </button>
  );
}

function TweetExplorer({ dashboard, dashboardConfig }) {
  const tableTweets = getWidgetData(dashboardConfig, 'tweet_table', []);
  const [tweets, setTweets] = useState(tableTweets);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [sentiment, setSentiment] = useState('all');
  const [target, setTarget] = useState('all');
  const [feedbackState, setFeedbackState] = useState({});

  useEffect(() => {
    setTweets(tableTweets);
  }, [dashboardConfig]);

  useEffect(() => {
    if (!dashboard?.id) return;
    setLoading(true);
    api.get(`/dashboards/${dashboard.id}/tweets`, { params: { limit: 3000 } })
      .then((response) => setTweets(response.data?.tweets || tableTweets))
      .catch(() => setTweets(tableTweets))
      .finally(() => setLoading(false));
  }, [dashboard?.id]);

  const targets = useMemo(() => {
    const map = new Map();
    tweets.forEach((tweet) => {
      if (tweet.target_id) map.set(String(tweet.target_id), tweet.target_name || `Cible ${tweet.target_id}`);
    });
    return Array.from(map.entries());
  }, [tweets]);

  const filteredTweets = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return tweets.filter((tweet) => {
      const matchesSearch = !needle
        || String(tweet.text || '').toLowerCase().includes(needle)
        || String(tweet.author || '').toLowerCase().includes(needle)
        || String(tweet.target_name || '').toLowerCase().includes(needle);
      const matchesSentiment = sentiment === 'all' || tweet.sentiment === sentiment;
      const matchesTarget = target === 'all' || String(tweet.target_id) === target;
      return matchesSearch && matchesSentiment && matchesTarget;
    });
  }, [tweets, search, sentiment, target]);

  const updateTweetSentiment = (tweetId, payload) => {
    setTweets((current) => current.map((tweet) => {
      if (Number(tweet.tweet_id) !== Number(tweetId)) return tweet;
      return {
        ...tweet,
        sentiment: payload.sentiment ?? tweet.sentiment,
        confidence: payload.confidence ?? tweet.confidence,
        analyzed_at: new Date().toISOString(),
      };
    }));
  };

  const handleFeedback = async (tweet) => {
    const tweetId = tweet.tweet_id;
    if (!tweetId || feedbackState[tweetId]?.loading) return;

    setFeedbackState((current) => ({
      ...current,
      [tweetId]: { loading: true, message: '' },
    }));

    try {
      const first = await api.post('/feedback/sentiment', {
        tweet_id: tweetId,
        satisfied: false,
        reason: 'Correction depuis le dashboard tweets',
      });
      const firstData = first.data || {};
      updateTweetSentiment(tweetId, firstData);

      let message = firstData.message || 'Feedback enregistré';
      const mustChooseLabel = firstData.requires_correction && !firstData.previous_sentiment;

      if (mustChooseLabel) {
        const allowed = firstData.allowed_labels || SENTIMENTS;
        const corrected = window.prompt(
          `Quelle est la bonne émotion ? Valeurs possibles : ${allowed.join(', ')}`,
          tweet.sentiment || 'neutre'
        );

        if (corrected) {
          const normalized = corrected.trim().toLowerCase();
          if (!allowed.includes(normalized)) {
            message = `Emotion invalide : ${normalized}`;
          } else {
            const correction = await api.post('/feedback/sentiment', {
              tweet_id: tweetId,
              satisfied: false,
              corrected_label: normalized,
              reason: 'Correction manuelle depuis le dashboard tweets',
            });
            const correctionData = correction.data || {};
            updateTweetSentiment(tweetId, correctionData);
            message = correctionData.message || 'Correction enregistrée';
          }
        }
      }

      setFeedbackState((current) => ({
        ...current,
        [tweetId]: { loading: false, message },
      }));
    } catch (error) {
      const detail = error?.response?.data?.detail;
      setFeedbackState((current) => ({
        ...current,
        [tweetId]: {
          loading: false,
          message: typeof detail === 'string' ? detail : 'Feedback impossible',
          error: true,
        },
      }));
    }
  };

  return (
    <section className="generated-widget-card generated-tweet-explorer">
      <div className="generated-widget-header generated-tweet-header">
        <div>
          <h2>Tous les tweets</h2>
          <p>Recherche plein texte, filtre par cible et par sentiment. Les dates affichent le tweet, la récupération et l'analyse.</p>
        </div>
        <span>{filteredTweets.length}/{tweets.length} tweets</span>
      </div>
      <div className="generated-filter-row">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Rechercher dans les tweets, auteurs, cibles..."
        />
        <select value={sentiment} onChange={(event) => setSentiment(event.target.value)}>
          <option value="all">Tous les sentiments</option>
          {SENTIMENTS.map((item) => <option key={item} value={item}>{SENTIMENT_LABELS[item]}</option>)}
        </select>
        <select value={target} onChange={(event) => setTarget(event.target.value)}>
          <option value="all">Toutes les cibles</option>
          {targets.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
        </select>
      </div>
      {loading && <p className="generated-muted">Chargement des tweets complets...</p>}
      <div className="generated-tweet-table-wrap">
        <table className="generated-tweet-table">
          <thead>
            <tr>
              <th>Cible</th>
              <th>Tweet</th>
              <th>Sentiment</th>
              <th>Confiance</th>
              <th>Date tweet</th>
              <th>Récupéré</th>
              <th>Feedback</th>
            </tr>
          </thead>
          <tbody>
            {filteredTweets.slice(0, 500).map((tweet) => (
              <tr key={tweet.tweet_id || tweet.twitter_id}>
                <td>
                  <strong>{tweet.target_name || '-'}</strong>
                  <span>@{tweet.author || '?'}</span>
                </td>
                <td>{tweet.text}</td>
                <td><SentimentBadge sentiment={tweet.sentiment} /></td>
                <td>{percent(tweet.confidence)}</td>
                <td>{formatDate(tweet.tweet_created_at || tweet.created_at || tweet.display_date)}</td>
                <td>{formatDate(tweet.collected_at || tweet.analyzed_at)}</td>
                <td>
                  <FeedbackButton
                    tweet={tweet}
                    disabled={Boolean(feedbackState[tweet.tweet_id]?.loading)}
                    onFeedback={handleFeedback}
                  />
                  {feedbackState[tweet.tweet_id]?.message && (
                    <span className={`generated-feedback-message ${feedbackState[tweet.tweet_id]?.error ? 'is-error' : ''}`}>
                      {feedbackState[tweet.tweet_id].message}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {filteredTweets.length > 500 && (
        <p className="generated-muted">Affichage limité aux 500 premiers résultats filtrés pour garder la page fluide.</p>
      )}
    </section>
  );
}

export default function GeneratedDashboardRenderer({ dashboard, config }) {
  const dashboardConfig = config || dashboard?.config_json || dashboard?.dashboard_config;
  if (!dashboardConfig) {
    return <p className="generated-empty">Aucune configuration de dashboard disponible.</p>;
  }

  const distributionWidget = getWidget(dashboardConfig, 'sentiment_distribution');
  const insightWidget = getWidget(dashboardConfig, 'insight_summary');
  const comparisonWidget = getWidget(dashboardConfig, 'target_comparison');
  const timelineWidget = getWidget(dashboardConfig, 'sentiment_timeline');
  const keywordWidget = getWidget(dashboardConfig, 'keyword_topics');
  const summaryWidget = getWidget(dashboardConfig, 'collection_summary');
  const metrics = buildTargetMetrics(distributionWidget, insightWidget);

  return (
    <div className="generated-dashboard-renderer">
      <header className="generated-dashboard-hero">
        <div>
          <p className="generated-dashboard-kicker">Dashboard analytique SentiFlow</p>
          <h1>{dashboard?.title || dashboardConfig.title || 'Dashboard généré'}</h1>
          <p className="generated-dashboard-question">
            Question : {dashboard?.question || dashboardConfig.source_question || 'Non renseignée'}
          </p>
        </div>
        <div className="generated-dashboard-date">
          <span>Créé le</span>
          <strong>{formatDate(dashboard?.created_at || dashboardConfig.generated_at || dashboardConfig.saved_at)}</strong>
        </div>
      </header>

      <CollectionSummary widget={summaryWidget} dashboardConfig={dashboardConfig} />
      {metrics.length > 0 && <DashboardMetrics metrics={metrics} summary={summaryWidget?.data} />}
      <InsightSummaryWidget widget={insightWidget} />

      <div className="generated-dashboard-two-col">
        <SentimentDonutWidget widget={distributionWidget} />
        <SentimentStackWidget distributionWidget={distributionWidget} />
      </div>

      <TargetComparisonWidget comparisonWidget={comparisonWidget} distributionWidget={distributionWidget} />
      <TargetQualityMapWidget metrics={metrics} />
      <SentimentTimelineWidget widget={timelineWidget} />

      <div className="generated-dashboard-two-col">
        <KeywordWordCloudWidget widget={keywordWidget} />
        <KeywordSentimentMatrixWidget widget={keywordWidget} />
      </div>
      <KeywordTopicsWidget widget={keywordWidget} />
      <TweetExplorer dashboard={dashboard} dashboardConfig={dashboardConfig} />

      {dashboard?.answer && (
        <section className="generated-widget-card generated-answer-card">
          <div className="generated-widget-header">
            <h2>Synthèse LLM</h2>
          </div>
          <p>{dashboard.answer}</p>
        </section>
      )}
    </div>
  );
}
