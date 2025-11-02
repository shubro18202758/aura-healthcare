import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // Don't send credentials
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aura_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth endpoints
export const login = async (email, password) => {
  const formData = new FormData();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await axios.post(`${API_BASE_URL}/auth/token`, formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

export const register = async (email, password, full_name, role) => {
  const response = await api.post('/auth/register', {
    email,
    password,
    full_name,
    role,
  });
  return response.data;
};

// Conversation endpoints
export const createConversation = async (patientId, language = 'en', initialMessage = null) => {
  const response = await api.post('/chat/conversations', {
    patient_id: patientId,
    language,
    initial_message: initialMessage,
  });
  return response.data;
};

export const getConversation = async (conversationId) => {
  const response = await api.get(`/chat/conversations/${conversationId}`);
  return response.data;
};

export const sendMessage = async (conversationId, message, language = 'en') => {
  const response = await api.post(`/chat/conversations/${conversationId}/messages`, {
    message,
    language,
  });
  return response.data;
};

// Patient endpoints
export const getPatientProfile = async () => {
  const response = await api.get('/patients/profile');
  return response.data;
};

export const getPatientConversations = async () => {
  const response = await api.get('/patients/conversations');
  return response.data;
};

export const getPatientReports = async () => {
  const response = await api.get('/patients/reports');
  return response.data;
};

export const getDashboardStats = async () => {
  const response = await api.get('/patients/dashboard/stats');
  return response.data;
};

// Doctor endpoints
export const getDoctorProfile = async () => {
  const response = await api.get('/doctors/profile');
  return response.data;
};

export const getDoctorPatients = async () => {
  const response = await api.get('/doctors/patients');
  return response.data;
};

export const getDoctorStats = async () => {
  const response = await api.get('/doctors/me/stats');
  return response.data;
};

export const getPatientHistory = async (patientId) => {
  const response = await api.get(`/doctors/patients/${patientId}/history`);
  return response.data;
};

// Reports endpoints
export const generateReport = async (conversationId) => {
  const response = await api.post(`/reports/generate/${conversationId}`);
  return response.data;
};

export const autoGenerateReport = async (conversationId) => {
  const response = await api.post(`/reports/auto-generate/${conversationId}`);
  return response.data;
};

export const getReport = async (reportId) => {
  const response = await api.get(`/reports/${reportId}`);
  return response.data;
};

// Report Analysis endpoints (Doctor AI Assistant)
export const analyzeReport = async (reportId, query, context = null) => {
  const response = await api.post(`/reports/analyze/${reportId}`, {
    query,
    context
  });
  return response.data;
};

export const summarizeReport = async (reportId, summaryType = 'brief') => {
  const response = await api.post(`/reports/summarize/${reportId}`, {
    summary_type: summaryType
  });
  return response.data;
};

export const compareReports = async (reportId1, reportId2, focusAreas = null) => {
  const response = await api.post('/reports/compare', {
    report_id_1: reportId1,
    report_id_2: reportId2,
    focus_areas: focusAreas
  });
  return response.data;
};

// Medical Documents endpoints
export const uploadMedicalDocument = async (conversationId, file, documentType, description, tags) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('conversation_id', conversationId);
  formData.append('document_type', documentType);
  if (description) formData.append('description', description);
  if (tags && tags.length > 0) {
    tags.forEach(tag => formData.append('tags', tag));
  }
  
  const response = await api.post('/medical-documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getMedicalDocuments = async (conversationId = null, documentType = null) => {
  const params = {};
  if (conversationId) params.conversation_id = conversationId;
  if (documentType) params.document_type = documentType;
  
  const response = await api.get('/medical-documents/', { params });
  return response.data;
};

export const getMedicalDocument = async (documentId) => {
  const response = await api.get(`/medical-documents/${documentId}`);
  return response.data;
};

export const deleteMedicalDocument = async (documentId) => {
  const response = await api.delete(`/medical-documents/${documentId}`);
  return response.data;
};

export const getDocumentSummary = async (conversationId) => {
  const response = await api.get(`/medical-documents/conversation/${conversationId}/summary`);
  return response.data;
};

// TTS (Text-to-Speech) endpoints
export const getAvailableVoices = async () => {
  const response = await api.get('/tts/voices');
  return response.data;
};

export const getTTSPreferences = async () => {
  const response = await api.get('/tts/preferences');
  return response.data;
};

export const updateTTSPreferences = async (preferences) => {
  const response = await api.put('/tts/preferences', preferences);
  return response.data;
};

export const setDefaultVoice = async (voiceType) => {
  const response = await api.post(`/tts/set-voice/${voiceType}`);
  return response.data;
};

export const convertTextToSpeech = async (text, voiceType = 'sara', language = 'en') => {
  const response = await api.post('/tts/convert', {
    text,
    voice_type: voiceType,
    language,
  });
  return response.data;
};

export default api;
