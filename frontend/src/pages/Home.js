import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ArrowRight, TrendingUp, BarChart3, MessageSquare, ShieldCheck,
  Sparkles, Star, Quote,
} from 'lucide-react';

const ACCENT = '#5271ff';

const HERO_IMG = 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1100&q=80';

const BENEFITS = [
  { icon: <TrendingUp size={22} />, title: 'Anticipez les tendances', desc: "Repérez les sujets qui montent et les signaux faibles avant vos concurrents." },
  { icon: <ShieldCheck size={22} />, title: 'Protégez votre e-réputation', desc: "Détectez les crises dès les premiers signaux négatifs et réagissez à temps." },
  { icon: <BarChart3 size={22} />, title: 'Décidez avec des données', desc: "Des tableaux de bord clairs : corrélations, tendances, comparaisons de sujets." },
  { icon: <MessageSquare size={22} />, title: 'Posez vos questions', desc: "Un assistant IA répond en langage naturel à partir des conversations réelles." },
];

const FEATURES = [
  {
    title: 'Analyse de sentiment en temps réel',
    desc: "SentiFlow collecte automatiquement les publications sur vos marques, hashtags et concurrents, puis détecte l'émotion dominante : joie, colère, peur, tristesse…",
    img: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=900&q=80',
  },
  {
    title: 'Des dashboards qui parlent',
    desc: "KPIs, évolution dans le temps, comparaison de sujets, carte des familles d'opinion et alertes. Conçu pour les analystes marketing, RH et BI — sans jargon.",
    img: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=900&q=80',
  },
  {
    title: 'Rapports prêts à partager',
    desc: "Chaque analyse génère un rapport exportable en PDF, à présenter en réunion ou à transmettre à vos équipes en un clic.",
    img: 'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=900&q=80',
  },
];

const TESTIMONIALS = [
  {
    name: 'Angel Hu', role: 'Directrice Marketing Digital',
    avatar: 'https://i.pravatar.cc/120?img=47',
    text: "SentiFlow a changé notre façon de travailler. On capte les tendances et les bad buzz en temps réel — on a évité deux crises ce trimestre. L'outil le plus utile de notre stack.",
  },
  {
    name: 'Sloan Marriott', role: "Responsable e-réputation",
    avatar: 'https://i.pravatar.cc/120?img=12',
    text: "Les dashboards sont d'une clarté rare : même mes équipes non techniques comprennent en un coup d'œil. On suit notre image et celle des concurrents sans effort. Je recommande à 100%.",
  },
  {
    name: 'Camille Renaud', role: 'Analyste Marketing',
    avatar: 'https://i.pravatar.cc/120?img=32',
    text: "Je pose une question à l'assistant, j'obtiens la synthèse et le rapport PDF derrière. Un gain de temps énorme sur mes reportings hebdomadaires. Bluffant de simplicité.",
  },
];

export default function Home() {
  const { user } = useAuth();
  const primaryTo = user ? '/assistant' : '/login';
  const primaryLabel = user ? "Ouvrir l'assistant" : 'Essayer gratuitement';

  return (
    <div style={{ margin: '-36px -44px', background: '#ffffff', color: '#0f172a' }}>
      {/* Top marketing nav */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '18px 40px', borderBottom: '1px solid #eef2f7', position: 'sticky', top: 0,
        background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(8px)', zIndex: 20,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontWeight: 800, fontSize: '1.15rem' }}>
          <img src="/logo.png" alt="SentiFlow" style={{ width: 28, height: 28, borderRadius: 7 }} />
          SentiFlow
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 22, fontSize: '0.9rem' }}>
          <a href="#features" style={{ color: '#475569' }}>Fonctionnalités</a>
          <a href="#pricing" style={{ color: '#475569' }}>Tarifs</a>
          <Link to="/about" style={{ color: '#475569' }}>À propos</Link>
          <Link to={primaryTo} style={{ background: ACCENT, color: '#fff', padding: '9px 18px', borderRadius: 8, fontWeight: 600 }}>
            {user ? 'Mon espace' : 'Se connecter'}
          </Link>
        </div>
      </div>

      {/* HERO */}
      <section style={{
        display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: 40, alignItems: 'center',
        padding: '70px 40px', background: 'linear-gradient(180deg, #f5f7ff 0%, #ffffff 100%)',
      }}>
        <div>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, background: '#eef2ff',
            color: ACCENT, padding: '6px 12px', borderRadius: 20, fontSize: '0.8rem', fontWeight: 600,
            border: `1px solid ${ACCENT}33`,
          }}>
            <Sparkles size={14} /> Analyse d'opinion propulsée par l'IA
          </span>
          <h1 style={{ fontSize: '3rem', fontWeight: 800, lineHeight: 1.1, margin: '18px 0 16px', letterSpacing: '-0.03em' }}>
            Comprenez ce que le monde<br />pense de vous.
          </h1>
          <p style={{ color: '#475569', fontSize: '1.1rem', lineHeight: 1.7, maxWidth: 520, marginBottom: 28 }}>
            SentiFlow analyse en temps réel les conversations sur vos marques, sujets et concurrents.
            Sentiment, tendances, alertes et rapports — tout au même endroit.
          </p>
          <div style={{ display: 'flex', gap: 12 }}>
            <Link to={primaryTo} style={{ background: ACCENT, color: '#fff', padding: '13px 24px', borderRadius: 10, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              {primaryLabel} <ArrowRight size={18} />
            </Link>
            <Link to="/pricing" style={{ background: '#fff', color: '#0f172a', padding: '13px 24px', borderRadius: 10, fontWeight: 600, border: '1px solid #e2e8f0' }}>
              Voir les offres
            </Link>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 18, color: '#64748b', fontSize: '0.85rem' }}>
            <Star size={15} color="#fbbf24" fill="#fbbf24" /> 4,8/5 — utilisé par des équipes marketing & RH
          </div>
        </div>
        <div style={{ borderRadius: 16, overflow: 'hidden', boxShadow: '0 20px 60px rgba(82,113,255,0.25)', background: '#e2e8f0' }}>
          <img src={HERO_IMG} alt="Dashboard SentiFlow" style={{ width: '100%', display: 'block' }} />
        </div>
      </section>

      {/* BENEFITS */}
      <section style={{ padding: '64px 40px', maxWidth: 1100, margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', fontSize: '2rem', fontWeight: 800, marginBottom: 10 }}>Pourquoi SentiFlow ?</h2>
        <p style={{ textAlign: 'center', color: '#64748b', marginBottom: 40 }}>Transformez le bruit des réseaux en décisions concrètes.</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 18 }}>
          {BENEFITS.map((b, i) => (
            <div key={i} style={{ background: '#fff', border: '1px solid #eef2f7', borderRadius: 14, padding: 22, boxShadow: '0 4px 16px rgba(15,23,42,0.04)' }}>
              <div style={{ width: 44, height: 44, borderRadius: 10, background: '#eef2ff', color: ACCENT, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 14 }}>{b.icon}</div>
              <h3 style={{ fontSize: '1.05rem', marginBottom: 6 }}>{b.title}</h3>
              <p style={{ color: '#64748b', fontSize: '0.88rem', lineHeight: 1.6 }}>{b.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES (alternating) */}
      <section id="features" style={{ padding: '20px 40px 64px', maxWidth: 1100, margin: '0 auto' }}>
        {FEATURES.map((f, i) => (
          <div key={i} style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 40, alignItems: 'center',
            margin: '40px 0',
            direction: i % 2 ? 'rtl' : 'ltr',
          }}>
            <div style={{ direction: 'ltr' }}>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: 12 }}>{f.title}</h3>
              <p style={{ color: '#475569', fontSize: '1rem', lineHeight: 1.7 }}>{f.desc}</p>
            </div>
            <div style={{ direction: 'ltr', borderRadius: 14, overflow: 'hidden', boxShadow: '0 14px 40px rgba(15,23,42,0.10)', background: '#e2e8f0' }}>
              <img src={f.img} alt={f.title} style={{ width: '100%', display: 'block' }} />
            </div>
          </div>
        ))}
      </section>

      {/* TESTIMONIALS */}
      <section style={{ padding: '64px 40px', background: '#f8fafc' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', fontSize: '2rem', fontWeight: 800, marginBottom: 10 }}>Ils en parlent mieux que nous</h2>
          <p style={{ textAlign: 'center', color: '#64748b', marginBottom: 40 }}>Retours d'expérience de nos utilisateurs.</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 18 }}>
            {TESTIMONIALS.map((t, i) => (
              <div key={i} style={{ background: '#fff', border: '1px solid #eef2f7', borderRadius: 14, padding: 24, boxShadow: '0 4px 16px rgba(15,23,42,0.04)' }}>
                <Quote size={26} color={ACCENT} style={{ opacity: 0.4, marginBottom: 10 }} />
                <p style={{ color: '#334155', fontSize: '0.94rem', lineHeight: 1.7, marginBottom: 18 }}>“{t.text}”</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <img src={t.avatar} alt={t.name} style={{ width: 44, height: 44, borderRadius: '50%', background: '#e2e8f0' }} />
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{t.name}</div>
                    <div style={{ color: '#94a3b8', fontSize: '0.8rem' }}>{t.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING TEASER */}
      <section id="pricing" style={{ padding: '64px 40px', textAlign: 'center' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: 10 }}>Une offre pour chaque besoin</h2>
        <p style={{ color: '#64748b', marginBottom: 28 }}>Commencez gratuitement, passez à la vitesse supérieure quand vous voulez.</p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16, flexWrap: 'wrap', marginBottom: 28 }}>
          {[['Free', '0€'], ['Standard', '19€'], ['Premium', '49€']].map(([n, p]) => (
            <div key={n} style={{ background: '#fff', border: n === 'Premium' ? `2px solid ${ACCENT}` : '1px solid #e2e8f0', borderRadius: 14, padding: '22px 30px', minWidth: 150 }}>
              <div style={{ fontWeight: 700, color: '#475569' }}>{n}</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, margin: '6px 0' }}>{p}<span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 500 }}>/mois</span></div>
            </div>
          ))}
        </div>
        <Link to="/pricing" style={{ background: ACCENT, color: '#fff', padding: '13px 28px', borderRadius: 10, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          Découvrir les offres <ArrowRight size={18} />
        </Link>
      </section>

      {/* FINAL CTA */}
      <section style={{ padding: '60px 40px', background: `linear-gradient(135deg, ${ACCENT} 0%, #7b93ff 100%)`, textAlign: 'center', color: '#fff' }}>
        <h2 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: 12 }}>Prêt à écouter votre audience ?</h2>
        <p style={{ opacity: 0.9, marginBottom: 24, fontSize: '1.05rem' }}>Lancez votre première analyse en moins de 2 minutes.</p>
        <Link to={primaryTo} style={{ background: '#fff', color: ACCENT, padding: '14px 30px', borderRadius: 10, fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          {primaryLabel} <ArrowRight size={18} />
        </Link>
      </section>

      {/* FOOTER */}
      <footer style={{ padding: '30px 40px', background: '#0f172a', color: '#94a3b8', textAlign: 'center', fontSize: '0.85rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, color: '#fff', fontWeight: 700, marginBottom: 8 }}>
          <img src="/logo.png" alt="SentiFlow" style={{ width: 22, height: 22, borderRadius: 6 }} /> SentiFlow
        </div>
        © {new Date().getFullYear()} SentiFlow — Analyse de sentiments. Tous droits réservés.
      </footer>
    </div>
  );
}
