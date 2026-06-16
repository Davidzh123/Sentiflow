import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Database, Cpu, MessageSquare, RefreshCw, BarChart3, Zap } from 'lucide-react';

const TEAM = [
  { name: "David", role: "Developpeur Full Stack", desc: "Architecture backend, RAG from scratch, integration LLM" },
  { name: "Louis Seillier", role: "ML / LLM", desc: "Planner TinyGPT from scratch, entrainement et evaluation des modeles" },
  { name: "Rym Fouzari", role: "Data / Analyse", desc: "Pipeline de donnees, analyses statistiques, dashboards analytiques" },
];

const PIPELINE_STEPS = [
  { icon: <MessageSquare size={20} />, title: "1. Question utilisateur", desc: "L'utilisateur pose une question en langage naturel sur les sentiments Twitter." },
  { icon: <Cpu size={20} />, title: "2. Planner LLM (TinyGPT)", desc: "Un Transformer decoder-only comprend l'intention, extrait les cibles et produit un plan JSON." },
  { icon: <Database size={20} />, title: "3. Retrieval from scratch", desc: "TF-IDF cosine + BM25 + RRF fusionnent les resultats. Query expansion dynamique via co-occurrences." },
  { icon: <RefreshCw size={20} />, title: "4. Re-ranking", desc: "Second passage : scoring contextuel, boost temporel, filtre confiance. Si pas assez → MCP Twitter temps reel." },
  { icon: <Zap size={20} />, title: "5. Generation (Groq)", desc: "Le prompt enrichi est envoye a Groq LLaMA 3 pour une reponse naturelle. Fallback sur TinyGPT si indisponible." },
  { icon: <BarChart3 size={20} />, title: "6. Dashboard + Metriques", desc: "Un dashboard est genere automatiquement. Metriques RAG (NDCG, MRR, faithfulness) calculees." },
];

export default function About() {
  return (
    <div className="animate-in" style={{ maxWidth: 800, margin: '0 auto' }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', paddingTop: 20, marginBottom: 48 }}>
        <h1 style={{ fontSize: '2rem', marginBottom: 12 }}>A propos de SentiFlow</h1>
        <p style={{ color: '#64748b', fontSize: '1rem', maxWidth: 600, margin: '0 auto' }}>
          Plateforme d'analyse de sentiments Twitter construite from scratch. 
          RAG maison, LLM specialise, generation via Groq — le tout sans dependance externe pour le retrieval.
        </p>
      </div>

      {/* Comment ca marche */}
      <section style={{ marginBottom: 56 }}>
        <h2 style={{ marginBottom: 24, fontSize: '1.3rem' }}>Comment ca marche</h2>
        <div style={{ display: 'grid', gap: 12 }}>
          {PIPELINE_STEPS.map((step, i) => (
            <div key={i} className="card" style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
              <div style={{ color: '#5271ff', marginTop: 2 }}>{step.icon}</div>
              <div>
                <h4 style={{ marginBottom: 4, fontSize: '0.92rem' }}>{step.title}</h4>
                <p style={{ color: '#64748b', fontSize: '0.84rem' }}>{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Qui sommes-nous */}
      <section style={{ marginBottom: 56 }}>
        <h2 style={{ marginBottom: 24, fontSize: '1.3rem' }}>Qui sommes-nous</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
          <div className="card">
            <h4 style={{ color: '#5271ff', marginBottom: 8 }}>Qui sommes-nous ?</h4>
            <p style={{ color: '#475569', fontSize: '0.86rem', lineHeight: 1.7 }}>
              Une équipe passionnée par l'IA et la donnée. Nous avons conçu SentiFlow pour rendre
              l'analyse d'opinion en ligne accessible, sans jargon technique.
            </p>
          </div>
          <div className="card">
            <h4 style={{ color: '#5271ff', marginBottom: 8 }}>Pourquoi SentiFlow ?</h4>
            <p style={{ color: '#475569', fontSize: '0.86rem', lineHeight: 1.7 }}>
              Comprendre ce que les gens pensent d'une marque, d'un sujet ou d'un événement prend
              un temps fou manuellement. SentiFlow automatise la collecte et l'analyse pour livrer
              des insights clairs en quelques secondes.
            </p>
          </div>
          <div className="card">
            <h4 style={{ color: '#5271ff', marginBottom: 8 }}>Notre objectif</h4>
            <p style={{ color: '#475569', fontSize: '0.86rem', lineHeight: 1.7 }}>
              Donner à chaque analyste marketing, RH ou BI une lecture fiable et visuelle de
              l'opinion publique — corrélations, tendances et alertes — pour décider plus vite et mieux.
            </p>
          </div>
        </div>
      </section>

      {/* Fonctionnalités clés */}
      <section style={{ marginBottom: 56 }}>
        <h2 style={{ marginBottom: 24, fontSize: '1.3rem' }}>Fonctionnalités clés</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
          {[
            { t: "Analyse en temps réel", d: "Collecte automatique des tweets et détection du sentiment (joie, colère, peur…) sur chaque sujet suivi." },
            { t: "Assistant IA", d: "Posez vos questions en langage naturel : l'assistant cherche, analyse et résume l'opinion pour vous." },
            { t: "Dashboard analytique", d: "KPIs, tendances, comparaisons, corrélations et carte des sujets — pensé pour les analystes marketing, RH et BI." },
            { t: "Alertes", d: "Soyez prévenu quand un sentiment dépasse un seuil sur une cible (e-réputation, gestion de crise)." },
            { t: "Rapports exportables", d: "Chaque analyse génère un rapport téléchargeable en PDF, prêt à partager." },
            { t: "Multi-utilisateurs & offres", d: "Comptes, abonnements et quotas adaptés à chaque profil d'utilisation." },
          ].map((f, i) => (
            <div key={i} className="card">
              <h4 style={{ color: '#5271ff', marginBottom: 8, fontSize: '0.95rem' }}>{f.t}</h4>
              <p style={{ color: '#475569', fontSize: '0.84rem', lineHeight: 1.6 }}>{f.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Equipe */}
      <section style={{ marginBottom: 56 }}>
        <h2 style={{ marginBottom: 24, fontSize: '1.3rem' }}>Equipe</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 14 }}>
          {TEAM.map((member, i) => (
            <div key={i} className="card" style={{ textAlign: 'center' }}>
              <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#5271ff', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', fontSize: '1.1rem', fontWeight: 700 }}>
                {member.name[0]}
              </div>
              <h4 style={{ marginBottom: 4 }}>{member.name}</h4>
              <p style={{ color: '#5271ff', fontSize: '0.78rem', marginBottom: 8 }}>{member.role}</p>
              <p style={{ color: '#64748b', fontSize: '0.8rem' }}>{member.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <Link to="/assistant" className="btn-primary">
          Essayer l'assistant <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
}
