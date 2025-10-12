import React from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Upload, 
  MessageSquare, 
  GitCompare, 
  AlertTriangle,
  TrendingUp,
  CheckCircle
} from 'lucide-react';
import { documentsAPI } from '../api/documents';
import { qaAPI } from '../api/qa';
import './Dashboard.css';

const Dashboard = () => {

  // Fetch documents
  const { data: documentsData, isLoading: documentsLoading } = useQuery(
    'documents',
    () => documentsAPI.getDocuments({ page: 1, size: 5 }),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  // Fetch Q&A sessions
  const { data: sessionsData, isLoading: sessionsLoading } = useQuery(
    'qa-sessions',
    () => qaAPI.getSessions(),
    {
      refetchInterval: 30000,
    }
  );

  // Calculate statistics
  const documents = documentsData?.documents || [];
  const sessions = sessionsData || [];
  
  const totalDocuments = documentsData?.total || 0;
  const processedDocuments = documents.filter(doc => doc.is_processed).length;
  const pendingDocuments = documents.filter(doc => doc.processing_status === 'pending').length;
  const failedDocuments = documents.filter(doc => doc.processing_status === 'failed').length;
  
  const totalQuestions = sessions.reduce((sum, session) => sum + session.total_questions, 0);
  const activeSessions = sessions.filter(session => session.is_active).length;

  const stats = [
    {
      title: 'Total Documents',
      value: totalDocuments,
      icon: FileText,
      color: 'blue',
      change: '+12%',
    },
    {
      title: 'Processed',
      value: processedDocuments,
      icon: CheckCircle,
      color: 'green',
      change: '+8%',
    },
    {
      title: 'Q&A Sessions',
      value: activeSessions,
      icon: MessageSquare,
      color: 'purple',
      change: '+15%',
    },
    {
      title: 'Total Questions',
      value: totalQuestions,
      icon: TrendingUp,
      color: 'orange',
      change: '+23%',
    },
  ];

  const quickActions = [
    {
      title: 'Upload Document',
      description: 'Upload a new legal document for analysis',
      icon: Upload,
      link: '/upload',
      color: 'blue',
    },
    {
      title: 'Start Q&A Session',
      description: 'Ask questions about your documents',
      icon: MessageSquare,
      link: '/qa',
      color: 'purple',
    },
    {
      title: 'Compare Documents',
      description: 'Compare two documents side by side',
      icon: GitCompare,
      link: '/compare',
      color: 'green',
    },
  ];

  const recentDocuments = documents.slice(0, 2);
  const recentSessions = sessions.slice(0, 2);

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <p className="dashboard-subtitle">
          Welcome back! Here's what's happening with your legal documents.
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="stats-grid">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className={`stat-card stat-card-${stat.color}`}>
              <div className="stat-icon">
                <Icon size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value">{stat.value}</div>
                <div className="stat-title">{stat.title}</div>
                <div className="stat-change">{stat.change}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="dashboard-section">
        <h2 className="section-title">Quick Actions</h2>
        <div className="quick-actions-grid">
          {quickActions.map((action, index) => {
            const Icon = action.icon;
            return (
              <Link key={index} to={action.link} className={`quick-action-card quick-action-${action.color}`}>
                <div className="quick-action-icon">
                  <Icon size={32} />
                </div>
                <div className="quick-action-content">
                  <h3 className="quick-action-title">{action.title}</h3>
                  <p className="quick-action-description">{action.description}</p>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      <div className="dashboard-content">
        {/* Recent Documents */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2 className="section-title">Recent Documents</h2>
            <Link to="/documents" className="section-link">
              View All
            </Link>
          </div>
          
          {documentsLoading ? (
            <div className="loading-skeleton">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton-item" />
              ))}
            </div>
          ) : recentDocuments.length > 0 ? (
            <div className="sessions-list">
              {recentDocuments.map((document) => (
                <div key={document.id} className="session-item">
                  <div className="session-icon">
                    <FileText size={20} />
                  </div>
                  <div className="session-content">
                    <h3 className="session-title">{document.title}</h3>
                    <p className="session-meta">
                      {document.document_type || 'Document'}
                    </p>
                    <div className="session-status">
                      <span className={`status-badge status-${document.processing_status}`}>
                        {document.processing_status}
                      </span>
                    </div>
                  </div>
                  <div className="session-actions">
                    <Link to={`/document/${document.id}`} className="btn btn-sm btn-outline">
                      View
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <FileText size={48} className="empty-icon" />
              <h3 className="empty-title">No documents yet</h3>
              <p className="empty-description">
                Upload your first legal document to get started.
              </p>
              <Link to="/upload" className="btn btn-primary">
                Upload Document
              </Link>
            </div>
          )}
        </div>

        {/* Recent Q&A Sessions */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2 className="section-title">Recent Q&A Sessions</h2>
            <Link to="/qa" className="section-link">
              View All
            </Link>
          </div>
          
          {sessionsLoading ? (
            <div className="loading-skeleton">
              {[...Array(2)].map((_, i) => (
                <div key={i} className="skeleton-item" />
              ))}
            </div>
          ) : recentSessions.length > 0 ? (
            <div className="sessions-list">
              {recentSessions.map((session) => (
                <div key={session.id} className="session-item">
                  <div className="session-icon">
                    <MessageSquare size={20} />
                  </div>
                  <div className="session-content">
                    <h3 className="session-title">{session.session_name}</h3>
                    <p className="session-meta">
                      {session.total_questions} questions • {session.is_active ? 'Active' : 'Inactive'}
                    </p>
                    <div className="session-status">
                      <span className={`status-badge ${session.is_active ? 'status-completed' : 'status-pending'}`}>
                        {session.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                  <div className="session-actions">
                    <Link to={`/qa/${session.id}`} className="btn btn-sm btn-outline">
                      Open
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <MessageSquare size={48} className="empty-icon" />
              <h3 className="empty-title">No Q&A sessions yet</h3>
              <p className="empty-description">
                Start a conversation with your documents.
              </p>
              <Link to="/qa" className="btn btn-primary">
                Start Session
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Alerts */}
      {pendingDocuments > 0 && (
        <div className="alert alert-warning">
          <AlertTriangle size={20} />
          <div className="alert-content">
            <h4 className="alert-title">Documents Processing</h4>
            <p className="alert-description">
              {pendingDocuments} document{pendingDocuments !== 1 ? 's' : ''} {pendingDocuments !== 1 ? 'are' : 'is'} currently being processed.
            </p>
          </div>
        </div>
      )}

      {failedDocuments > 0 && (
        <div className="alert alert-error">
          <AlertTriangle size={20} />
          <div className="alert-content">
            <h4 className="alert-title">Processing Errors</h4>
            <p className="alert-description">
              {failedDocuments} document{failedDocuments !== 1 ? 's' : ''} failed to process. Please check and retry.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
