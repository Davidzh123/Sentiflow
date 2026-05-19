import React, { useEffect, useState } from 'react';
import { getTargets, askLlm } from '../services/api';

export default function AssistantLLM() {
  const [targets, setTargets] = useState([]);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Salut, pose-moi une question sur tes comptes ou hashtags déjà collectés. Exemple : Résume l'activité de #Minecraft sur les derniers jours.",
    },
  ]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTargets();
  }, []);

  const loadTargets = async () => {
    try {
      const response = await getTargets();
      setTargets(response.data);
    } catch (err) {
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: "Impossible de charger les cibles. Vérifie que tu es connecté.",
        },
      ]);
    }
  };

  const detectTargetIds = (text) => {
    const lower = text.toLowerCase();

    const mentioned = targets.filter((target) => {
      const name = String(target.name || '').toLowerCase();
      const query = String(target.query || '').toLowerCase();

      return (
        (name && lower.includes(name)) ||
        (query && lower.includes(query)) ||
        (name.startsWith('#') && lower.includes(name.slice(1))) ||
        (name.startsWith('@') && lower.includes(name.slice(1)))
      );
    });

    if (mentioned.length > 0) {
      return mentioned.map((target) => target.id);
    }

    return targets.map((target) => target.id);
  };

  const handleAsk = async () => {
    const cleanQuestion = question.trim();

    if (!cleanQuestion || loading) return;

    if (targets.length === 0) {
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content:
            "Tu n'as pas encore de cible. Crée d'abord un compte ou un hashtag dans la page Cibles.",
        },
      ]);
      return;
    }

    const userMessage = {
      role: 'user',
      content: cleanQuestion,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion('');
    setLoading(true);

    try {
      const targetIds = detectTargetIds(cleanQuestion);

      const response = await askLlm({
        question: cleanQuestion,
        target_ids: targetIds,
        days: 7,
        generate_dashboard: true,
      });

      const data = response.data;

      let content = data.answer || "Je n'ai pas réussi à générer de réponse.";

      if (data.dashboard_config) {
        content += "\n\nDashboard généré : oui.";
      }

      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content,
          raw: data,
        },
      ]);
    } catch (err) {
      console.error(err);

      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content:
            err.response?.data?.detail ||
            "Erreur pendant l'appel au LLM. Regarde les logs de l'API pour voir l'erreur exacte.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleAsk();
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <h1>Assistant LLM SentiFlow</h1>

      <div
        style={{
          height: '65vh',
          overflowY: 'auto',
          border: '1px solid #2a2f3a',
          borderRadius: 12,
          padding: 16,
          background: '#0f141c',
          marginBottom: 16,
        }}
      >
        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              justifyContent:
                message.role === 'user' ? 'flex-end' : 'flex-start',
              marginBottom: 12,
            }}
          >
            <div
              style={{
                maxWidth: '75%',
                padding: '10px 14px',
                borderRadius: 12,
                whiteSpace: 'pre-line',
                background:
                  message.role === 'user' ? '#2563eb' : '#1f2937',
                color: 'white',
              }}
            >
              {message.content}
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ color: '#9ca3af' }}>
            Le LLM analyse les données...
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Pose une question : Compare #Minecraft et #love, résume #trump, montre les tweets les plus négatifs..."
          rows={2}
          style={{
            flex: 1,
            resize: 'none',
            borderRadius: 10,
            padding: 12,
          }}
        />

        <button
          onClick={handleAsk}
          disabled={loading}
          style={{
            borderRadius: 10,
            padding: '0 20px',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          Envoyer
        </button>
      </div>

      <p style={{ color: '#9ca3af', fontSize: 13 }}>
        Cibles disponibles automatiquement :{' '}
        {targets.length > 0
          ? targets.map((target) => target.name).join(', ')
          : 'aucune'}
      </p>
    </div>
  );
}