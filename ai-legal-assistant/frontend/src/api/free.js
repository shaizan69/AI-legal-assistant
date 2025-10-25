import api from './index';

// Free API endpoints for anonymous users
export const freeAPI = {
  // Upload document
  uploadDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/free/upload', formData, {
      headers: { 
        'apikey': process.env.REACT_APP_SUPABASE_ANON_KEY
      },
    });
  },

  // Create session
  createSession: async (documentId) => {
    return api.post('/free/session', { document_id: documentId });
  },

  // Ask question
  askQuestion: async (sessionId, question) => {
    return api.post('/free/ask', { session_id: sessionId, question });
  },

  // Analyze risks
  analyzeRisks: async (sessionId) => {
    return api.post('/free/analyze-risks', { session_id: sessionId });
  },

  // Delete session
  deleteSession: async (sessionId) => {
    return api.delete(`/free/session/${sessionId}`);
  },

  // End session (alias for deleteSession for compatibility)
  endSession: async (sessionId) => {
    return api.delete(`/free/session/${sessionId}`);
  },
};

export default freeAPI;
