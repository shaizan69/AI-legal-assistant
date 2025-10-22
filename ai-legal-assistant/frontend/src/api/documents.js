import api from './index';

export const documentsAPI = {
  uploadDocument: async (file, metadata = {}) => {
    try {
      // Simple upload using the working free/upload endpoint
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/free/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000, // 30 seconds timeout
      });

      return response.data;
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
  },

  getDocuments: async (params = {}) => {
    const response = await api.get('/upload/', { params });
    return response.data;
  },

  getDocument: async (documentId) => {
    const response = await api.get(`/upload/${documentId}`);
    return response.data;
  },

  deleteDocument: async (documentId) => {
    const response = await api.delete(`/upload/${documentId}`);
    return response.data;
  },

  getSummary: async (documentId) => {
    const response = await api.get(`/summarize/${documentId}`);
    return response.data;
  },

  generateSummary: async (documentId, options = {}) => {
    const response = await api.post('/summarize/', {
      document_id: documentId,
      ...options,
    });
    return response.data;
  },

  getRisks: async (documentId) => {
    const response = await api.get(`/risks/${documentId}`);
    return response.data;
  },

  detectRisks: async (documentId, options = {}) => {
    const response = await api.post('/risks/', {
      document_id: documentId,
      ...options,
    });
    return response.data;
  },

  compareDocuments: async (document1Id, document2Id, options = {}) => {
    const response = await api.post('/compare/', {
      document1_id: document1Id,
      document2_id: document2Id,
      ...options,
    });
    return response.data;
  },

  getComparisons: async () => {
    const response = await api.get('/compare/');
    return response.data;
  },

  getComparison: async (comparisonId) => {
    const response = await api.get(`/compare/${comparisonId}`);
    return response.data;
  },

  deleteComparison: async (comparisonId) => {
    const response = await api.delete(`/compare/${comparisonId}`);
    return response.data;
  },
};
