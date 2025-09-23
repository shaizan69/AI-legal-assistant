import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock the AuthProvider to avoid authentication issues in tests
jest.mock('./contexts/AuthContext', () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    isAuthenticated: false,
  }),
  AuthProvider: ({ children }) => children,
}));

test('renders app without crashing', () => {
  render(<App />);
  // The app should render without throwing any errors
});
