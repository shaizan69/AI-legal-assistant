import api from './index';

export const qaAPI = {
  createSession: async (documentId, sessionName = null) => {
    const response = await api.post('/qa/sessions', {
      document_id: documentId,
      session_name: sessionName,
    });
    return response.data;
  },

  getSessions: async () => {
    const response = await api.get('/qa/sessions');
    return response.data;
  },

  getSession: async (sessionId) => {
    const response = await api.get(`/qa/sessions/${sessionId}`);
    return response.data;
  },

  deleteSession: async (sessionId) => {
    const response = await api.delete(`/qa/sessions/${sessionId}`);
    return response.data;
  },

  cleanupSession: async (sessionId) => {
    const response = await api.post(`/qa/sessions/${sessionId}/cleanup`);
    return response.data;
  },

  askQuestion: async (question, sessionId) => {
    const response = await api.post('/qa/ask', {
      question,
      session_id: sessionId,
    }, {
      timeout: 180000, // 3 minutes timeout for LLM requests
    });
    return response.data;
  },

  getSessionQuestions: async (sessionId) => {
    const response = await api.get(`/qa/sessions/${sessionId}/questions`);
    return response.data;
  },

  provideFeedback: async (questionId, isHelpful, rating = null, feedback = null) => {
    const response = await api.put(`/qa/questions/${questionId}/feedback`, {
      is_helpful: isHelpful,
      rating,
      feedback,
    });
    return response.data;
  },
};
