import api from './index';
import { uploadFile, generateFilePath, getFileUrl } from '../config/supabase';

export const documentsAPI = {
  uploadDocument: async (file, metadata = {}) => {
    try {
      // Get current user ID from token (robust to non-JWT tokens)
      const token = localStorage.getItem('token');
      let userId = 'anonymous';
      if (token && token.includes('.')) {
        try {
          const base64Url = token.split('.')[1];
          const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
          const jsonPayload = decodeURIComponent(
            atob(base64)
              .split('')
              .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
              .join('')
          );
          const payload = JSON.parse(jsonPayload);
          userId = payload.sub || payload.user_id || payload.email || userId;
        } catch (e) {
          // Fallback to anonymous if decoding fails
          userId = 'anonymous';
        }
      }

      if (!userId) userId = 'anonymous';

      // Generate unique file path
      const filePath = generateFilePath(userId, file.name);

      // Always upload via edge function using service role to avoid RLS issues
      const form = new FormData();
      form.append('file', file);
      form.append('path', filePath);
      const { data: direct } = await api.post('/upload/direct', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 180000, // 3 minutes for large files
        maxBodyLength: Infinity,
        maxContentLength: Infinity,
      });
      const uploadResult = { path: direct.path };
      
      // Get public URL
      const fileUrl = getFileUrl(filePath);

      // Send metadata to backend
      const response = await api.post('/upload/supabase', {
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
