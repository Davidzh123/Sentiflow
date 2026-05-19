import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Cibles from './pages/Cibles';
import Alertes from './pages/Alertes';
import Admin from './pages/Admin';
import AssistantLLM from './pages/AssistantLLM';
function PrivateRoute({ children }) {
  const { token, loading } = useAuth();
  if (loading) return <p>Chargement...</p>;
  return token ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/cibles" element={<PrivateRoute><Cibles /></PrivateRoute>} />
            <Route path="/alertes" element={<PrivateRoute><Alertes /></PrivateRoute>} />
            <Route path="/admin" element={<PrivateRoute><Admin /></PrivateRoute>} />
            <Route  path="/assistant" element={<PrivateRoute><AssistantLLM /></PrivateRoute>}/>
          </Routes>
        </Layout>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
