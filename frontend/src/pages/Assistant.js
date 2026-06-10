import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { assistantChat } from '../services/api';

export default function Assistant() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Salut ! Je suis l'assistant SentiFlow.\n\n" +
        "Tu peux me demander :\n" +
        "• **Collecter** : \"récupère les tweets avec #france\" → je collecte, analyse et stocke\n" +
        "• **Analyser** : \"quel est le sentiment sur #trump ?\" → je cherche et réponds\n" +
        "• **Comparer** : \"compare #love et #politique\" → je compare les sentiments\n\n" +
        "Je décide automatiquement s'il faut aller chercher sur Twitter ou si j'ai déjà les données.",
    },
  ]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleAsk = async () => {
    const q = question.trim();
    if (!q || loading) return;

    setMessages((prev) => [...prev, { role: 'user', content: q }]);
    setQuestion('');
    setLoading(true);

    try {
      const response = await assistantChat({ question: q, enable_mcp: true });
      const data = response.data;

      // Badge du mode utilisé
      const modeBadge = data.mode === 'agent'
        ? '🤖 Agent (collecte + dashboard)'
        : '🔍 RAG (recherche intelligente)';

      // Infos techniques
      const techInfo = [];
      if (data.mode === 'agent') {
        const log = (data.execution_log || []).map(step => {
          if (step.action === 'collect_tweets') return `📥 ${step.target}: ${step.saved || 0} tweets`;
          if (step.action === 'analyze_sentiments') return `🤖 ${step.target}: ${step.analyzed || 0} analysés`;
          if (step.action === 'create_target') return `✅ Cible créée: ${step.target}`;
          if (step.action === 'reuse_target') return `♻️ Cible existante: ${step.target}`;
          return null;
        }).filter(Boolean);
        if (log.length) techInfo.push(log.join('\n'));
      } else {
        if (data.total_retrieved) techInfo.push(`📊 ${data.total_retrieved} tweets trouvés`);
        if (data.mcp_used) techInfo.push(`🐦 Twitter temps réel utilisé`);
        if (data.generator) techInfo.push(`💬 Générateur: ${data.generator}`);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer || "Pas de réponse.",
          mode: data.mode,
          modeBadge,
          techInfo: techInfo.join('\n'),
          dashboardId: data.dashboard_id,
          dashboardUrl: data.dashboard_url,
          sources: data.sources,
          plan: data.plan,
        },
      ]);
    } catch (err) {
      const detail = err?.response?.data?.detail || err.message || 'Erreur inconnue';
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `❌ Erreur : ${typeof detail === 'string' ? detail : JSON.stringify(detail)}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div style={{ maxWidth: 980, margin: '0 auto', height: 'calc(100vh - 60px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ marginBottom: 12 }}>
        <h1 style={{ marginBottom: 4 }}>🧠 Assistant SentiFlow</h1>
        <p style={{ color: '#9ca3af', margin: 0, fontSize: 13 }}>
          Pipeline unifié : Planner LLM from scratch → Agent (collecte) OU RAG (recherche) → MCP Twitter → Groq
        </p>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          border: '1px solid #2a2f3a',
          borderRadius: 14,
          padding: 16,
          background: '#0f141c',
          marginBottom: 14,
        }}
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              marginBottom: 12,
            }}
          >
            <div
              style={{
                maxWidth: '80%',
                padding: '12px 14px',
                borderRadius: 14,
                whiteSpace: 'pre-line',
                background: msg.role === 'user' ? '#2563eb' : '#1f2937',
                color: 'white',
                lineHeight: 1.5,
              }}
            >
              {/* Badge du mode */}
              {msg.modeBadge && (
                <div style={{
                  fontSize: 11,
                  padding: '3px 8px',
                  borderRadius: 6,
                  background: msg.mode === 'agent' ? '#7f1d1d' : '#064e3b',
                  display: 'inline-block',
                  marginBottom: 8,
                }}>
                  {msg.modeBadge}
                </div>
              )}

              {msg.content}

              {/* Dashboard link */}
              {msg.dashboardUrl && (
                <div style={{ marginTop: 12 }}>
                  <Link
                    to={msg.dashboardUrl}
                    style={{
                      padding: '8px 12px',
                      borderRadius: 8,
                      background: '#ef4444',
                      color: 'white',
                      textDecoration: 'none',
                      fontWeight: 700,
                      fontSize: 13,
                    }}
                  >
                    📊 Voir le dashboard
                  </Link>
                </div>
              )}

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <details style={{ marginTop: 10, color: '#d1d5db' }}>
                  <summary style={{ cursor: 'pointer', fontSize: 12 }}>📋 Sources ({msg.sources.length} tweets)</summary>
                  <div style={{ fontSize: 11, marginTop: 6 }}>
                    {msg.sources.map((s, j) => (
                      <div key={j} style={{ marginBottom: 4, padding: '3px 6px', background: '#111827', borderRadius: 4 }}>
                        <strong>@{s.author}</strong> → {s.sentiment} ({Math.round((s.confidence || 0) * 100)}%)
                      </div>
                    ))}
                  </div>
                </details>
              )}

              {/* Tech info */}
              {msg.techInfo && (
                <details style={{ marginTop: 8, color: '#d1d5db' }}>
                  <summary style={{ cursor: 'pointer', fontSize: 12 }}>⚙️ Détails techniques</summary>
                  <pre style={{ fontSize: 11, marginTop: 4, whiteSpace: 'pre-wrap' }}>{msg.techInfo}</pre>
                </details>
              )}

              {/* Plan LLM */}
              {msg.plan && (
                <details style={{ marginTop: 8, color: '#d1d5db' }}>
                  <summary style={{ cursor: 'pointer', fontSize: 12 }}>🧠 Plan LLM</summary>
                  <pre style={{ fontSize: 10, marginTop: 4 }}>{JSON.stringify(msg.plan, null, 2)}</pre>
                </details>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ color: '#9ca3af', marginTop: 8 }}>
            🔄 En cours (planner → agent/rag → mcp → réponse)...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: 10 }}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ex: récupère les tweets avec #france / quel est le sentiment sur #trump / compare #love et #psg"
          rows={2}
          style={{
            flex: 1,
            resize: 'none',
            borderRadius: 12,
            padding: 12,
            background: '#111827',
            color: 'white',
            border: '1px solid #374151',
            outline: 'none',
          }}
        />
        <button
          onClick={handleAsk}
          disabled={loading}
          style={{
            borderRadius: 12,
            padding: '0 22px',
            cursor: loading ? 'not-allowed' : 'pointer',
            background: loading ? '#4b5563' : '#10b981',
            color: 'white',
            border: 'none',
            fontWeight: 700,
          }}
        >
          Envoyer
        </button>
      </div>
    </div>
  );
}
