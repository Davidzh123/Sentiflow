import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

// Ajouter le token JWT à chaque requête
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Rediriger vers login si 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (email, password) =>
  api.post('/auth/login', { email, password });

export const register = (email, username, password) =>
  api.post('/auth/register', { email, username, password });

export const getMe = () => api.get('/auth/me');

// Targets
export const getTargets = () => api.get('/targets/');
export const createTarget = (name, target_type) =>
  api.post('/targets/', { name, target_type });
export const deleteTarget = (id) => api.delete(`/targets/${id}`);

// Twitter
export const verifyTarget = (id) => api.get(`/twitter/verify/${id}`);
export const collectTweets = (id) =>
  api.post(`/twitter/collect/${id}`, null, { timeout: 60000 });

// Analysis
export const analyzeTweets = (id) =>
  api.post(`/analysis/${id}/analyze`, null, { timeout: 120000 });
export const getAnalysis = (id, days = 7) =>
  api.get(`/analysis/${id}`, { params: { days } });

// Tweets
export const getTweets = (id, limit = 50) =>
  api.get(`/tweets/${id}`, { params: { limit } });

// Alerts
export const getAlerts = () => api.get('/alerts/');
export const createAlert = (data) => api.post('/alerts/', data);

// Tasks (Celery)
export const triggerCollectAll = () => api.post('/tasks/collect-all');
export const triggerAnalyzeAll = () => api.post('/tasks/analyze-all');

// RAG Chat
export const ragChat = (question, target_id = null) =>
  api.post('/rag/chat', { question, target_id }, { timeout: 60000 });
export const ragIndex = () => api.post('/rag/index', null, { timeout: 120000 });

// Monitoring
export const getMonitoringStats = (hours = 24) =>
  api.get('/monitoring/stats', { params: { hours } });
export const checkDrift = (target_id = null) =>
  api.get('/monitoring/drift', { params: { target_id } });

export default api;
