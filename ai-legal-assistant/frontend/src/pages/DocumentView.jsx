import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { Download, Share2, MessageSquare } from 'lucide-react';
import { documentsAPI } from '../api/documents';
import { qaAPI } from '../api/qa';
import './DocumentView.css';

const DocumentView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [startingQA, setStartingQA] = useState(false);
  
  const { data: document, isLoading } = useQuery(
    ['document', id],
    () => documentsAPI.getDocument(id),
    {
      enabled: !!id,
      refetchOnWindowFocus: true,
      // Poll until processing completes so the UI updates as soon as backend finishes
      refetchInterval: (data) => {
        if (!data) return 2000;
        return data.is_processed ? false : 2000;
      },
    }
  );

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading document...</p>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="error-container">
        <h2>Document not found</h2>
        <p>The document you're looking for doesn't exist or you don't have permission to view it.</p>
      </div>
    );
  }

  // Use direct public Supabase URL for inline preview (bucket is public)
  const viewerSrc = document.file_url;

  return (
    <div className="document-view">
      <div className="document-header">
        <div className="document-info">
          <h1 className="document-title">{document.title}</h1>
           <div className="document-meta">
             <span className="document-type">{document.document_type || 'Document'}</span>
             <span className="document-date">
               Uploaded {new Date(document.created_at).toLocaleDateString()}
             </span>
             <span className="document-status" style={{marginLeft: 8, fontSize: 12, color: document.is_processed ? '#059669' : '#92400e'}}>
               {document.is_processed ? 'Processed' : 'Processing…'}
             </span>
           </div>
        </div>
        <div className="document-actions">
          <a 
            href={document.file_url} 
            download={document.original_filename}
            className="btn btn-outline"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Download size={16} />
            Download
          </a>
          <button className="btn btn-outline">
            <Share2 size={16} />
            Share
          </button>
          <button 
            className="btn btn-primary"
            onClick={async () => {
              if (startingQA) return;
              try {
                setStartingQA(true);
                const session = await qaAPI.createSession(Number(id));
                navigate(`/qa/${session.id}`);
              } catch (e) {
                console.error('Failed to start Q&A session', e);
                alert('Unable to start Q&A session. Please ensure the document has finished processing.');
              } finally {
                setStartingQA(false);
              }
            }}
            disabled={startingQA}
          >
            <MessageSquare size={16} />
            {startingQA ? 'Starting…' : 'Start Q&A'}
          </button>
        </div>
      </div>

      <div className="document-content">
        <div className="document-viewer">
          <h3>Document Viewer</h3>
          <div className="document-frame">
            {document.file_url ? (
              <div>
                <div className="document-controls" style={{padding: '1rem', background: '#f8fafc', marginBottom: '1rem', borderRadius: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                  <div>
                    <p><strong>File:</strong> {document.original_filename}</p>
                    <p><strong>Type:</strong> {document.mime_type}</p>
                  </div>
                  <div style={{display: 'flex', gap: '0.5rem'}}>
                    <a 
                      href={document.file_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn btn-sm btn-outline"
                    >
                      Open in New Tab
                    </a>
                    <a 
                      href={document.file_url} 
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-sm btn-primary"
                    >
                      Download
                    </a>
                  </div>
                </div>
                
                {/** Prefer backend redirect endpoint for PDFs to avoid cross-origin embedding issues */}
                <div className="document-preview">
                  {document.mime_type === 'application/pdf' ? (
                    <div className="pdf-viewer">
                      <object
                        data={viewerSrc}
                        type="application/pdf"
                        width="100%"
                        height="600px"
                        style={{border: '1px solid #e5e7eb', borderRadius: '0.5rem'}}
                      >
                        <div className="pdf-fallback" style={{padding: '2rem', textAlign: 'center', border: '1px solid #e5e7eb', borderRadius: '0.5rem', background: '#fafafa'}}>
                          <p style={{marginBottom: '1rem'}}>PDF preview not available in your browser.</p>
                          <a 
                            href={viewerSrc} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="btn btn-primary"
                          >
                            Open PDF in New Tab
                          </a>
                        </div>
                      </object>
                    </div>
                  ) : document.mime_type.startsWith('image/') ? (
                    <div className="image-viewer" style={{textAlign: 'center'}}>
                      <img 
                        src={document.file_url} 
                        alt={document.title}
                        style={{maxWidth: '100%', height: 'auto', border: '1px solid #e5e7eb', borderRadius: '0.5rem'}}
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.nextSibling.style.display = 'block';
                        }}
                      />
                      <div style={{display: 'none', padding: '2rem', background: '#fee2e2', color: '#dc2626', borderRadius: '0.5rem'}}>
                        <p>Image could not be loaded.</p>
                      </div>
                    </div>
                  ) : document.mime_type.startsWith('text/') ? (
                    <div className="text-viewer">
                      <iframe
                        src={document.file_url}
                        title={document.title}
                        className="document-iframe"
                        width="100%"
                        height="600px"
                        style={{border: '1px solid #e5e7eb', borderRadius: '0.5rem'}}
                      />
                    </div>
                  ) : (
                    <div className="generic-viewer" style={{padding: '2rem', textAlign: 'center', border: '1px solid #e5e7eb', borderRadius: '0.5rem', background: '#fafafa'}}>
                      <p style={{marginBottom: '1rem'}}>Preview not available for this file type.</p>
                      <a 
                        href={document.file_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="btn btn-primary"
                      >
                        Open File
                      </a>
                    </div>
                  )}
                </div>
                
                {document.extracted_text && (
                  <div className="extracted-text" style={{marginTop: '2rem', padding: '1.5rem', background: '#f8fafc', borderRadius: '0.5rem'}}>
                    <h4 style={{marginBottom: '1rem', color: '#374151'}}>Extracted Text Content</h4>
                    <div style={{maxHeight: '300px', overflow: 'auto', padding: '1rem', background: 'white', border: '1px solid #e5e7eb', borderRadius: '0.25rem', fontSize: '0.875rem', lineHeight: '1.5', whiteSpace: 'pre-wrap'}}>
                      {document.extracted_text}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="no-document" style={{padding: '2rem', textAlign: 'center', border: '1px solid #e5e7eb', borderRadius: '0.5rem', background: '#fafafa'}}>
                <p>Document not available for viewing.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentView;
