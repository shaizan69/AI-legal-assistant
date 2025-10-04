import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Upload, 
  Search, 
  Eye,
  MessageSquare,
  Trash2
} from 'lucide-react';
import { documentsAPI } from '../api/documents';
import { toast } from 'react-toastify';
import './Home.css';

const Home = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [page, setPage] = useState(1);
  const [selectedDocuments, setSelectedDocuments] = useState([]);

  // Helper function to format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Fetch documents
  const { data: documentsData, isLoading, refetch } = useQuery(
    ['documents', page, searchTerm, filterType, sortBy],
    () => documentsAPI.getDocuments({
      page,
      size: 10,
      search: searchTerm,
      document_type: filterType !== 'all' ? filterType : undefined,
      sort_by: sortBy,
    }),
    {
      keepPreviousData: true,
    }
  );

  const documents = documentsData?.documents || [];
  const totalPages = documentsData?.pages || 1;

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setPage(1);
  };

  const handleFilterChange = (e) => {
    setFilterType(e.target.value);
    setPage(1);
  };

  const handleSortChange = (e) => {
    setSortBy(e.target.value);
    setPage(1);
  };

  const handleSelectDocument = (documentId) => {
    setSelectedDocuments(prev => 
      prev.includes(documentId) 
        ? prev.filter(id => id !== documentId)
        : [...prev, documentId]
    );
  };

  const handleSelectAll = () => {
    if (selectedDocuments.length === documents.length) {
      setSelectedDocuments([]);
    } else {
      setSelectedDocuments(documents.map(doc => doc.id));
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await documentsAPI.deleteDocument(documentId);
        toast.success('Document deleted successfully');
        refetch();
      } catch (error) {
        toast.error('Failed to delete document');
      }
    }
  };

  const handleBulkDelete = async () => {
    if (selectedDocuments.length === 0) return;
    
    if (window.confirm(`Are you sure you want to delete ${selectedDocuments.length} document(s)?`)) {
      try {
        await Promise.all(selectedDocuments.map(id => documentsAPI.deleteDocument(id)));
        toast.success(`${selectedDocuments.length} document(s) deleted successfully`);
        setSelectedDocuments([]);
        refetch();
      } catch (error) {
        toast.error('Failed to delete documents');
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'status-completed';
      case 'processing': return 'status-processing';
      case 'failed': return 'status-failed';
      default: return 'status-pending';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="home">
      <div className="home-header">
        <h1 className="home-title">Documents</h1>
        <div className="home-actions">
          <Link to="/upload" className="btn btn-primary">
            <Upload size={20} />
            Upload Document
          </Link>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="search-filters">
        <div className="search-bar">
          <Search size={20} className="search-icon" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchTerm}
            onChange={handleSearch}
            className="search-input"
          />
        </div>
        
        <div className="filters">
          <select
            value={filterType}
            onChange={handleFilterChange}
            className="filter-select"
          >
            <option value="all">All Types</option>
            <option value="contract">Contract</option>
            <option value="agreement">Agreement</option>
            <option value="terms">Terms</option>
            <option value="policy">Policy</option>
            <option value="other">Other</option>
          </select>
          
          <select
            value={sortBy}
            onChange={handleSortChange}
            className="filter-select"
          >
            <option value="created_at">Newest First</option>
            <option value="-created_at">Oldest First</option>
            <option value="title">Title A-Z</option>
            <option value="-title">Title Z-A</option>
            <option value="word_count">Word Count</option>
          </select>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedDocuments.length > 0 && (
        <div className="bulk-actions">
          <span className="bulk-count">
            {selectedDocuments.length} document(s) selected
          </span>
          <div className="bulk-buttons">
            <button
              onClick={handleBulkDelete}
              className="btn btn-danger btn-sm"
            >
              <Trash2 size={16} />
              Delete Selected
            </button>
            <button
              onClick={() => setSelectedDocuments([])}
              className="btn btn-outline btn-sm"
            >
              Clear Selection
            </button>
          </div>
        </div>
      )}

      {/* Documents Table */}
      <div className="documents-container">
        {isLoading ? (
          <div className="loading-skeleton">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        ) : documents.length > 0 ? (
          <div className="documents-table">
            <div className="table-header">
              <div className="table-cell checkbox-cell">
                <input
                  type="checkbox"
                  checked={selectedDocuments.length === documents.length && documents.length > 0}
                  onChange={handleSelectAll}
                  className="checkbox"
                />
              </div>
              <div className="table-cell">Document</div>
              <div className="table-cell">Type</div>
              <div className="table-cell">Status</div>
              <div className="table-cell">Size</div>
              <div className="table-cell">Created</div>
              <div className="table-cell">Actions</div>
            </div>
            
            {documents.map((document) => (
              <div key={document.id} className="table-row">
                <div className="table-cell checkbox-cell">
                  <input
                    type="checkbox"
                    checked={selectedDocuments.includes(document.id)}
                    onChange={() => handleSelectDocument(document.id)}
                    className="checkbox"
                  />
                </div>
                
                <div className="table-cell document-cell">
                  <div className="document-info">
                    <div className="document-title">{document.title}</div>
                    <div className="document-meta">
                      {document.document_type || 'Document'} • {formatFileSize(document.file_size)}
                    </div>
                  </div>
                </div>
                
                <div className="table-cell">
                  <span className="document-type">
                    {document.document_type || 'Unknown'}
                  </span>
                </div>
                
                <div className="table-cell">
                  <span className={`status-badge ${getStatusColor(document.processing_status)}`}>
                    {document.processing_status}
                  </span>
                </div>
                
                <div className="table-cell">
                  {formatFileSize(document.file_size)}
                </div>
                
                <div className="table-cell">
                  {formatDate(document.created_at)}
                </div>
                
                <div className="table-cell actions-cell">
                  <div className="actions-menu">
                    <Link
                      to={`/document/${document.id}`}
                      className="action-btn"
                      title="View Document"
                    >
                      <Eye size={16} />
                    </Link>
                    <Link
                      to={`/qa?document=${document.id}`}
                      className="action-btn"
                      title="Start Q&A"
                    >
                      <MessageSquare size={16} />
                    </Link>
                    <button
                      onClick={() => handleDeleteDocument(document.id)}
                      className="action-btn danger"
                      title="Delete Document"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <FileText size={64} className="empty-icon" />
            <h3 className="empty-title">No documents found</h3>
            <p className="empty-description">
              {searchTerm || filterType !== 'all' 
                ? 'No documents match your search criteria.'
                : 'Upload your first document to get started.'
              }
            </p>
            <Link to="/upload" className="btn btn-primary">
              <Upload size={20} />
              Upload Document
            </Link>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="pagination-btn"
          >
            Previous
          </button>
          
          <div className="pagination-info">
            Page {page} of {totalPages}
          </div>
          
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="pagination-btn"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default Home;
