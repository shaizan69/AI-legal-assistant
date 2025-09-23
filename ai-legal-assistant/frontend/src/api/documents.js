import api from './index';
import { uploadFile, generateFilePath, getFileUrl } from '../config/supabase';

export const documentsAPI = {
  uploadDocument: async (file, metadata = {}) => {
    try {
      // Get current user ID from token
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      // Decode token to get user ID (simple base64 decode for JWT payload)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const userId = payload.sub || payload.user_id;

      if (!userId) {
        throw new Error('User ID not found in token');
      }

      // Generate unique file path
      const filePath = generateFilePath(userId, file.name);

      // Upload file to Supabase Storage
      const uploadResult = await uploadFile(file, filePath);
      
      // Get public URL
      const fileUrl = getFileUrl(filePath);

      // Send metadata to backend
      const response = await api.post('/api/upload/supabase', {
        filename: uploadResult.path,
        original_filename: file.name,
        file_path: filePath,
        file_url: fileUrl,
        file_size: file.size,
        mime_type: file.type,
        title: metadata.title || file.name.replace(/\.[^/.]+$/, ""),
        document_type: metadata.document_type || 'contract',
        description: metadata.description || '',
        supabase_path: uploadResult.path
      });

      return response.data;
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
  },

  getDocuments: async (params = {}) => {
    const response = await api.get('/api/upload/', { params });
    return response.data;
  },

  getDocument: async (documentId) => {
    const response = await api.get(`/api/upload/${documentId}`);
    return response.data;
  },

  deleteDocument: async (documentId) => {
    const response = await api.delete(`/api/upload/${documentId}`);
    return response.data;
  },

  getSummary: async (documentId) => {
    const response = await api.get(`/api/summarize/${documentId}`);
    return response.data;
  },

  generateSummary: async (documentId, options = {}) => {
    const response = await api.post('/api/summarize/', {
      document_id: documentId,
      ...options,
    });
    return response.data;
  },

  getRisks: async (documentId) => {
    const response = await api.get(`/api/risks/${documentId}`);
    return response.data;
  },

  detectRisks: async (documentId, options = {}) => {
    const response = await api.post('/api/risks/', {
      document_id: documentId,
      ...options,
    });
    return response.data;
  },

  compareDocuments: async (document1Id, document2Id, options = {}) => {
    const response = await api.post('/api/compare/', {
      document1_id: document1Id,
      document2_id: document2Id,
      ...options,
    });
    return response.data;
  },

  getComparisons: async () => {
    const response = await api.get('/api/compare/');
    return response.data;
  },

  getComparison: async (comparisonId) => {
    const response = await api.get(`/api/compare/${comparisonId}`);
    return response.data;
  },

  deleteComparison: async (comparisonId) => {
    const response = await api.delete(`/api/compare/${comparisonId}`);
    return response.data;
  },
};
