import api from './index';

export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', {
      username: email,
      password,
    });
    return response.data;
  },

  signup: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  updateUser: async (userData) => {
    const response = await api.put('/auth/me', userData);
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },

  refreshToken: async () => {
    const response = await api.post('/auth/refresh');
    return response.data;
  },
};
