import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  BarChart3, Target, Bell, Settings, LogOut,
  Home, LogIn, MessageSquare, LayoutDashboard, Info, Clock, Cpu,
  CreditCard, LifeBuoy, User as UserIcon, Menu,
} from 'lucide-react';
import { getUnreadCount } from '../services/api';
import './Layout.css';

function CollectTimer() {
  const [timeLeft, setTimeLeft] = useState('');
  const [lastCollect, setLastCollect] = useState(null);
  const [paused, setPaused] = useState(false);
  const [interval, setIntervalMin] = useState(15);
  const [pipelineInfo, setPipelineInfo] = useState(null);

  const checkStatus = () => {
    fetch('/admin/collect-timer')
      .then(r => r.json())
      .then(data => {
        setPaused(!data.active);
        setIntervalMin(data.interval_minutes || 15);
      })
      .catch(() => {});
    fetch('/admin/pipeline/timer')
      .then(r => r.json())
      .then(data => setPipelineInfo(data))
      .catch(() => {});
  };

  useEffect(() => {
    checkStatus();
    const statusInterval = window.setInterval(checkStatus, 10000);
    // Ecouter l'event custom pour refresh instantané
    const onRefresh = () => checkStatus();
    window.addEventListener('sentiflow:refresh-timer', onRefresh);
    return () => {
      window.clearInterval(statusInterval);
      window.removeEventListener('sentiflow:refresh-timer', onRefresh);
    };
  }, []);

  useEffect(() => {
    if (paused) { setTimeLeft(''); return; }
    const update = () => {
      const now = new Date();
      const totalSec = now.getMinutes() * 60 + now.getSeconds();
      const intervalSec = interval * 60;
      const elapsed = totalSec % intervalSec;
      const remaining = intervalSec - elapsed;
      const min = Math.floor(remaining / 60);
      const sec = remaining % 60;
      setTimeLeft(`${min}:${sec.toString().padStart(2, '0')}`);

      if (remaining <= 1 && !lastCollect) {
        setLastCollect('Tweets collectes et analyses');
        setTimeout(() => setLastCollect(null), 15000);
      }
    };
    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, [paused, interval, lastCollect]);

  return (
    <div>
      {!paused && (
        <div className="collect-timer">
          <Clock size={12} />
          <span>Collecte dans <strong>{timeLeft}</strong></span>
        </div>
      )}
      {pipelineInfo && pipelineInfo.next_train_in && (
        <div className="collect-timer" style={{ marginTop: 4 }}>
          <Cpu size={12} />
          <span>Training dans <strong>{pipelineInfo.next_train_in}</strong></span>
        </div>
      )}
      {pipelineInfo && pipelineInfo.last_result && (
        <div className="collect-notif" style={{
          marginTop: 4,
          background: pipelineInfo.last_result.replaced ? 'rgba(52,211,153,0.08)' : 'rgba(251,191,36,0.08)',
          borderColor: pipelineInfo.last_result.replaced ? 'rgba(52,211,153,0.15)' : 'rgba(251,191,36,0.15)',
          color: pipelineInfo.last_result.replaced ? '#34d399' : '#fbbf24',
        }}>
          TinyGPT: {pipelineInfo.last_result.replaced ? 'Nouveau modele actif' : 'Modele inchange'}
          {' '}({(pipelineInfo.last_result.new_score * 100).toFixed(0)}%)
        </div>
      )}
      {lastCollect && (
        <div className="collect-notif">
          {lastCollect}
        </div>
      )}
    </div>
  );
}

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [unread, setUnread] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    if (!user) return;
    const refresh = () => getUnreadCount().then((r) => setUnread(r.data?.unread || 0)).catch(() => {});
    refresh();
    const id = window.setInterval(refresh, 20000);
    window.addEventListener('sentiflow:refresh-notifs', refresh);
    return () => {
      window.clearInterval(id);
      window.removeEventListener('sentiflow:refresh-notifs', refresh);
    };
  }, [user]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const features = user?.features || {};
  let navItems;
  if (!user) {
    navItems = [
      { path: '/', icon: <Home size={18} />, label: 'Accueil' },
      { path: '/about', icon: <Info size={18} />, label: 'A propos' },
      { path: '/login', icon: <LogIn size={18} />, label: 'Connexion' },
    ];
  } else if (user.is_admin) {
    // Sidebar de CONTRÔLE pour l'admin (il pilote l'app, il ne l'utilise pas comme un client)
    navItems = [
      { path: '/', icon: <Home size={18} />, label: 'Accueil' },
      { path: '/admin', icon: <Settings size={18} />, label: 'Contrôle (Admin)' },
      { path: '/dashboard', icon: <BarChart3 size={18} />, label: 'Dashboard global' },
      { path: '/notifications', icon: <Bell size={18} />, label: 'Notifications', badge: unread },
      { path: '/profile', icon: <UserIcon size={18} />, label: 'Profil' },
      { path: '/about', icon: <Info size={18} />, label: 'A propos' },
    ];
  } else {
    navItems = [
      { path: '/', icon: <Home size={18} />, label: 'Accueil' },
      { path: '/assistant', icon: <MessageSquare size={18} />, label: 'Assistant IA' },
      ...(features.interactive_dashboard ? [{ path: '/dashboard', icon: <BarChart3 size={18} />, label: 'Dashboard' }] : []),
      { path: '/dashboards/generated', icon: <LayoutDashboard size={18} />, label: 'Mes rapports IA' },
      { path: '/cibles', icon: <Target size={18} />, label: 'Cibles' },
      ...(features.alerts ? [{ path: '/alertes', icon: <Bell size={18} />, label: 'Alertes' }] : []),
      { path: '/notifications', icon: <Bell size={18} />, label: 'Notifications', badge: unread },
      { path: '/pricing', icon: <CreditCard size={18} />, label: 'Tarifs' },
      { path: '/support', icon: <LifeBuoy size={18} />, label: 'Support' },
      { path: '/profile', icon: <UserIcon size={18} />, label: 'Profil' },
      { path: '/about', icon: <Info size={18} />, label: 'A propos' },
    ];
  }

  const isLanding = location.pathname === '/';
  const showSidebar = !isLanding && sidebarOpen;
  const mainStyle = (isLanding || !showSidebar) ? { marginLeft: 0 } : undefined;

  return (
    <div className="layout">
      {showSidebar && (
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-row">
            <img src="/logo.png" alt="SentiFlow" className="logo-img" />
            <div>
              <h2>SentiFlow</h2>
              <p className="subtitle">Analyse de sentiments</p>
            </div>
          </div>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              {item.icon}
              <span>{item.label}</span>
              {item.badge > 0 && (
                <span style={{
                  marginLeft: 'auto', background: '#f87171', color: '#fff',
                  fontSize: '0.66rem', fontWeight: 700, borderRadius: 10,
                  minWidth: 18, height: 18, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: '0 5px',
                }}>{item.badge > 99 ? '99+' : item.badge}</span>
              )}
            </Link>
          ))}
        </nav>
        {user && (
          <div className="sidebar-footer">
            <CollectTimer />
            <Link to="/profile" className="user-info" style={{ textDecoration: 'none' }} title="Voir mon profil">
              <div className="user-avatar">{user.username[0].toUpperCase()}</div>
              <div>
                <span className="user-name">{user.username}</span>
                {user.is_admin && <span className="badge">Admin</span>}
                {user.plan && (
                  <span className="badge" style={{
                    marginLeft: 4,
                    background: user.plan === 'premium' ? '#fbbf24' : user.plan === 'standard' ? '#5271ff' : '#cbd5e1',
                    color: user.plan === 'premium' ? '#1c1917' : '#fff',
                  }}>
                    {user.plan}
                  </span>
                )}
              </div>
            </Link>
            <button onClick={handleLogout} className="logout-btn">
              <LogOut size={16} />
              <span>Deconnexion</span>
            </button>
          </div>
        )}
      </aside>
      )}
      <main className="main-content" style={mainStyle}>
        {!isLanding && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            margin: '-36px -44px 26px', padding: '10px 18px',
            background: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(8px)',
            borderBottom: '1px solid #e2e8f0', position: 'sticky', top: -36, zIndex: 30,
          }}>
            <button
              onClick={() => setSidebarOpen((o) => !o)}
              title={sidebarOpen ? 'Masquer le menu' : 'Afficher le menu'}
              style={{
                width: 34, height: 34, borderRadius: 8, cursor: 'pointer', flexShrink: 0,
                background: '#f1f5f9', border: '1px solid #e2e8f0', color: '#1e293b',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              <Menu size={18} />
            </button>
            <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#0f172a', fontWeight: 700, flexShrink: 0 }}>
              <img src="/logo.png" alt="" style={{ width: 24, height: 24, borderRadius: 6 }} /> SentiFlow
            </Link>
            <nav style={{ display: 'flex', gap: 4, overflowX: 'auto', flex: 1, padding: '0 6px' }}>
              {navItems.map((item) => (
                <Link key={item.path} to={item.path} title={item.label}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px', borderRadius: 8,
                    whiteSpace: 'nowrap', fontSize: '0.82rem',
                    color: location.pathname === item.path ? '#5271ff' : '#475569',
                    background: location.pathname === item.path ? 'rgba(82,113,255,0.1)' : 'transparent',
                  }}>
                  {item.icon}
                  <span>{item.label}</span>
                  {item.badge > 0 && (
                    <span style={{ background: '#f87171', color: '#fff', fontSize: '0.6rem', fontWeight: 700, borderRadius: 8, padding: '0 5px' }}>{item.badge}</span>
                  )}
                </Link>
              ))}
            </nav>
            {user ? (
              <button onClick={handleLogout} title="Déconnexion" style={{
                width: 34, height: 34, borderRadius: 8, cursor: 'pointer', flexShrink: 0,
                background: '#f1f5f9', border: '1px solid #e2e8f0', color: '#f87171',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <LogOut size={16} />
              </button>
            ) : (
              <Link to="/login" style={{ flexShrink: 0, background: '#5271ff', color: '#fff', padding: '7px 14px', borderRadius: 8, fontSize: '0.82rem', fontWeight: 600 }}>
                Connexion
              </Link>
            )}
          </div>
        )}
        {children}
      </main>
    </div>
  );
}
