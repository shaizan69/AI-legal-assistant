import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  FileText, 
  Upload, 
  MessageSquare, 
  GitCompare, 
  User, 
  LogOut, 
  Menu, 
  X,
  BarChart3,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import './Layout.css';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarMinimized, setSidebarMinimized] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
    { name: 'Documents', href: '/documents', icon: FileText },
    { name: 'Upload', href: '/upload', icon: Upload },
    { name: 'Q&A Sessions', href: '/qa', icon: MessageSquare },
    { name: 'Compare', href: '/compare', icon: GitCompare },
  ];

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="layout">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''} ${sidebarMinimized ? 'sidebar-minimized' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <FileText className="logo-icon" />
            {!sidebarMinimized && <span className="logo-text">Legal AI</span>}
          </div>
          <div className="sidebar-controls">
            <button
              className="sidebar-minimize-btn"
              onClick={() => setSidebarMinimized(!sidebarMinimized)}
              title={sidebarMinimized ? "Expand sidebar" : "Minimize sidebar"}
            >
              {sidebarMinimized ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
            </button>
            <button
              className="sidebar-close"
              onClick={() => setSidebarOpen(false)}
            >
              <X size={24} />
            </button>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`nav-item ${isActive(item.href) ? 'nav-item-active' : ''}`}
                onClick={() => setSidebarOpen(false)}
                title={sidebarMinimized ? item.name : ''}
              >
                <Icon size={20} />
                {!sidebarMinimized && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              <User size={20} />
            </div>
            {!sidebarMinimized && (
              <div className="user-details">
                <div className="user-name">{user?.full_name || user?.username}</div>
                <div className="user-email">{user?.email}</div>
              </div>
            )}
          </div>
          <button className="logout-btn" onClick={handleLogout} title={sidebarMinimized ? "Logout" : ""}>
            <LogOut size={20} />
            {!sidebarMinimized && <span>Logout</span>}
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className={`main-content ${sidebarMinimized ? 'sidebar-minimized' : ''}`}>
        {/* Top bar */}
        <header className="top-bar">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={24} />
          </button>
          
          <div className="top-bar-content">
            <h1 className="page-title">
              {location.pathname === '/' && 'Documents'}
              {location.pathname === '/dashboard' && 'Dashboard'}
              {location.pathname === '/upload' && 'Upload Document'}
              {location.pathname.startsWith('/document/') && 'Document Details'}
              {location.pathname.startsWith('/qa/') && 'Q&A Session'}
              {location.pathname === '/compare' && 'Compare Documents'}
            </h1>
          </div>
        </header>

        {/* Page content */}
        <main className="page-content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
