import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '';

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

// Compatible avec les deux styles : createTarget(name, type) ou createTarget({ name, target_type })
export const createTarget = (nameOrPayload, targetType) => {
  const payload =
    typeof nameOrPayload === 'object'
      ? nameOrPayload
      : { name: nameOrPayload, target_type: targetType };
  return api.post('/targets/', payload);
};

export const deleteTarget = (id) => api.delete(`/targets/${id}`);

// Twitter
export const verifyTarget = (id) => api.get(`/twitter/verify/${id}`);
export const collectTweets = (id) =>
  api.post(`/twitter/collect/${id}`, null, { timeout: 120000 });

// Analysis
export const analyzeTweets = (id) =>
  api.post(`/analysis/${id}/analyze`, null, { timeout: 180000 });
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

// LLM
export const askLlm = (data) =>
  api.post('/llm/ask', data, { timeout: 120000 });

export const askLlmAgent = (data) =>
  api.post('/llm/agent', data, { timeout: 240000 });

export const getLlmModelInfo = () => api.get('/llm/model-info');

// Feedback loop
export const sendSentimentFeedback = (data) =>
  api.post('/feedback/sentiment', data, { timeout: 60000 });

export const sendLlmFeedback = (data) =>
  api.post('/feedback/llm', data, { timeout: 180000 });

// Generated dashboards
export const getGeneratedDashboards = () => api.get('/dashboards/');
export const getGeneratedDashboard = (id) => api.get(`/dashboards/${id}`);
export const createGeneratedDashboard = (data) => api.post('/dashboards/', data);
export const deleteGeneratedDashboard = (id) => api.delete(`/dashboards/${id}`);

export default api;
