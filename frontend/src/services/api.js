import axios from 'axios';

const API_URL = '';

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

// Rediriger vers login si 401 (sauf pour les routes auth)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config?.url?.startsWith('/auth/')) {
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

export const resetPassword = (email, newPassword) =>
  api.post('/auth/reset-password', { email, new_password: newPassword });

export const getMe = () => api.get('/auth/me');
export const updateProfile = (data) => api.patch('/auth/profile', data);

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
export const collectTweets = (id, options = {}) =>
  api.post(`/twitter/collect/${id}`, null, {
    params: {
      days: options.days ?? 0,
      max_tweets: options.maxTweets ?? 20,
    },
    timeout: 300000,
  });

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

// RAG from scratch + MCP
export const ragChat = (data) =>
  api.post('/rag/chat', data, { timeout: 120000 });

export const ragIndex = (data) =>
  api.post('/rag/index', data || { days: 30 }, { timeout: 60000 });

export const ragInfo = () => api.get('/rag/info');

export const ragMcpTools = () => api.get('/rag/mcp/tools');

export const ragMcpCall = (toolName, args) =>
  api.post('/rag/mcp/call', { tool_name: toolName, arguments: args }, { timeout: 60000 });

export const ragEvaluate = (data) =>
  api.post('/rag/evaluate', data || { log_mlflow: true }, { timeout: 180000 });

// Assistant unifié (Agent + RAG automatique)
export const assistantChat = (data) =>
  api.post('/assistant/chat', data, { timeout: 240000 });

// Modèles de génération disponibles (sélecteur LLM)
export const getModels = () => api.get('/assistant/models');

// Historique des conversations
export const getConversations = () => api.get('/conversations');
export const createConversation = (title) => api.post('/conversations', { title });
export const getConversation = (id) => api.get(`/conversations/${id}`);
export const renameConversation = (id, title) => api.patch(`/conversations/${id}`, { title });
export const deleteConversation = (id) => api.delete(`/conversations/${id}`);

// Abonnement / Plan
export const getMyPlan = () => api.get('/auth/plan');

// Analytics (dashboard interactif pro)
export const getAnalyticsDashboard = (days = 30, targetIds = null) =>
  api.get('/analytics/dashboard', {
    params: { days, ...(targetIds ? { target_ids: targetIds.join(',') } : {}) },
    timeout: 60000,
  });

// Tickets de support
export const createTicket = (data) => api.post('/tickets', data);
export const getMyTickets = () => api.get('/tickets/mine');
export const adminAllTickets = (status) =>
  api.get('/tickets/admin/all', { params: status ? { status } : {} });
export const adminCountOpenTickets = () => api.get('/tickets/admin/count-open');
export const adminRespondTicket = (id, data) =>
  api.post(`/tickets/admin/${id}/respond`, data);

// Admin : logs questions + gestion plans
export const adminQuestionLogs = (limit = 100) =>
  api.get('/admin/question-logs', { params: { limit } });
export const adminListUsers = () => api.get('/admin/users');
export const adminSetUserPlan = (userId, plan) =>
  api.patch(`/admin/users/${userId}/plan`, { plan });

// Admin : modération / sécurité RAG
export const adminGetModeration = () => api.get('/admin/moderation');
export const adminAddBlockedWord = (word, category = 'custom') =>
  api.post('/admin/moderation', { word, category });
export const adminUpdateBlockedWord = (id, word, category = 'custom') =>
  api.put(`/admin/moderation/${id}`, { word, category });
export const adminDeleteBlockedWord = (id) => api.delete(`/admin/moderation/${id}`);

// Billing / abonnement (paiement simulé)
export const subscribePlan = (plan, cardName) =>
  api.post('/billing/subscribe', { plan, card_name: cardName });
export const getInvoices = () => api.get('/billing/invoices');

// Notifications
export const getNotifications = (limit = 50) =>
  api.get('/notifications/mine', { params: { limit } });
export const getUnreadCount = () => api.get('/notifications/unread-count');
export const markNotificationRead = (id) => api.post(`/notifications/${id}/read`);
export const markAllNotificationsRead = () => api.post('/notifications/read-all');

export default api;
