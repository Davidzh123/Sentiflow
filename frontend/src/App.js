import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Home from './pages/Home';
import About from './pages/About';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Cibles from './pages/Cibles';
import Alertes from './pages/Alertes';
import Admin from './pages/Admin';
import Assistant from './pages/Assistant';
import GeneratedDashboards from './pages/GeneratedDashboards';
import GeneratedDashboardDetail from './pages/GeneratedDashboardDetail';
import Pricing from './pages/Pricing';
import Support from './pages/Support';
import Profile from './pages/Profile';
import Notifications from './pages/Notifications';
import NotFound from './pages/NotFound';
import './App.css';

function PrivateRoute({ children }) {
  const { token, loading } = useAuth();
  if (loading) return <div style={{ padding: 60, color: '#94a3b8', textAlign: 'center' }}>Chargement...</div>;
  return token ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/cibles" element={<PrivateRoute><Cibles /></PrivateRoute>} />
            <Route path="/alertes" element={<PrivateRoute><Alertes /></PrivateRoute>} />
            <Route path="/admin" element={<PrivateRoute><Admin /></PrivateRoute>} />
            <Route path="/assistant" element={<PrivateRoute><Assistant /></PrivateRoute>} />
            <Route path="/pricing" element={<PrivateRoute><Pricing /></PrivateRoute>} />
            <Route path="/support" element={<PrivateRoute><Support /></PrivateRoute>} />
            <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
            <Route path="/notifications" element={<PrivateRoute><Notifications /></PrivateRoute>} />
            <Route path="/dashboards/generated" element={<PrivateRoute><GeneratedDashboards /></PrivateRoute>} />
            <Route path="/dashboards/generated/:id" element={<PrivateRoute><GeneratedDashboardDetail /></PrivateRoute>} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
