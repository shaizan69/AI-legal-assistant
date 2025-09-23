import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { GitCompare, FileText, ArrowRight } from 'lucide-react';
import { documentsAPI } from '../api/documents';

const CompareDocuments = () => {
  const [document1Id, setDocument1Id] = useState('');
  const [document2Id, setDocument2Id] = useState('');
  const [comparison, setComparison] = useState(null);

  // Fetch documents for selection
  const { data: documentsData } = useQuery(
    'documents-for-comparison',
    () => documentsAPI.getDocuments({ page: 1, size: 100 }),
  );

  const documents = documentsData?.documents || [];

  const handleCompare = async () => {
    if (!document1Id || !document2Id) {
      alert('Please select both documents to compare');
      return;
    }

    if (document1Id === document2Id) {
      alert('Please select different documents to compare');
      return;
    }

    try {
      const result = await documentsAPI.compareDocuments(document1Id, document2Id);
      setComparison(result);
    } catch (error) {
      console.error('Comparison failed:', error);
      alert('Failed to compare documents');
    }
  };

  const getDocumentById = (id) => {
    return documents.find(doc => doc.id === parseInt(id));
  };

  return (
    <div className="compare-documents">
      <div className="compare-header">
        <h1 className="compare-title">Compare Documents</h1>
        <p className="compare-subtitle">Compare two documents side by side</p>
      </div>

      <div className="compare-container">
        <div className="document-selection">
          <div className="document-selector">
            <label className="selector-label">First Document</label>
            <select
              value={document1Id}
              onChange={(e) => setDocument1Id(e.target.value)}
              className="document-select"
            >
              <option value="">Select a document...</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.title}
                </option>
              ))}
            </select>
            {document1Id && (
              <div className="selected-document">
                <FileText size={16} />
                <span>{getDocumentById(document1Id)?.title}</span>
              </div>
            )}
          </div>

          <div className="compare-arrow">
            <ArrowRight size={24} />
          </div>

          <div className="document-selector">
            <label className="selector-label">Second Document</label>
            <select
              value={document2Id}
              onChange={(e) => setDocument2Id(e.target.value)}
              className="document-select"
            >
              <option value="">Select a document...</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.title}
                </option>
              ))}
            </select>
            {document2Id && (
              <div className="selected-document">
                <FileText size={16} />
                <span>{getDocumentById(document2Id)?.title}</span>
              </div>
            )}
          </div>
        </div>

        <div className="compare-actions">
          <button
            onClick={handleCompare}
            disabled={!document1Id || !document2Id}
            className="btn btn-primary"
          >
            <GitCompare size={20} />
            Compare Documents
          </button>
        </div>

        {comparison && (
          <div className="comparison-results">
            <h3>Comparison Results</h3>
            <div className="comparison-content">
              <div className="comparison-section">
                <h4>Summary</h4>
                <p>{comparison.summary || 'No summary available'}</p>
              </div>
              
              <div className="comparison-section">
                <h4>Key Differences</h4>
                <ul>
                  {comparison.key_differences?.map((diff, index) => (
                    <li key={index}>{diff}</li>
                  )) || <li>No differences found</li>}
                </ul>
              </div>
              
              <div className="comparison-section">
                <h4>Similarities</h4>
                <ul>
                  {comparison.similarities?.map((similarity, index) => (
                    <li key={index}>{similarity}</li>
                  )) || <li>No similarities found</li>}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompareDocuments;
