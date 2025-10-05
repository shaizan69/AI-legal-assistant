import api from './index';

// Free API endpoints for anonymous users
export const freeAPI = {
  // Upload document
  uploadDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/free/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Create session
  createSession: async (documentId) => {
    return api.post('/api/free/sessions', { document_id: documentId });
  },

  // Ask question
  askQuestion: async (sessionId, question) => {
    return api.post('/api/free/ask', { session_id: sessionId, question });
  },

  // Analyze risks
  analyzeRisks: async (sessionId) => {
    return api.post('/api/free/analyze-risks', { session_id: sessionId });
  },

  // Delete session
  deleteSession: async (sessionId) => {
    return api.delete(`/api/free/sessions/${sessionId}`);
  },
};

export default freeAPI;
