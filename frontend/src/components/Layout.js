import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BarChart3, Target, Bell, Settings, LogOut, Home, LogIn, Bot } from 'lucide-react';
import './Layout.css';

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = user
    ? [
        { path: '/', icon: <Home size={20} />, label: 'Accueil' },
        { path: '/dashboard', icon: <BarChart3 size={20} />, label: 'Dashboard' },
        { path: '/dashboards/generated', icon: <BarChart3 size={20} />, label: 'Dashboards générés' },
        { path: '/cibles', icon: <Target size={20} />, label: 'Cibles' },
        { path: '/alertes', icon: <Bell size={20} />, label: 'Alertes' },
        { path: '/assistant', icon: <Bot size={20} />, label: 'Assistant LLM' },
        ...(user.is_admin ? [{ path: '/admin', icon: <Settings size={20} />, label: 'Admin' }] : []),
      ]
    : [
        { path: '/', icon: <Home size={20} />, label: 'Accueil' },
        { path: '/login', icon: <LogIn size={20} />, label: 'Connexion' },
      ];

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>📊 SentiFlow</h2>
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
            </Link>
          ))}
        </nav>
        {user && (
          <div className="sidebar-footer">
            <div className="user-info">
              <span>👤 {user.username}</span>
              {user.is_admin && <span className="badge">Admin</span>}
            </div>
            <button onClick={handleLogout} className="logout-btn">
              <LogOut size={18} /> Déconnexion
            </button>
          </div>
        )}
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}
