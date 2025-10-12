import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { 
  Upload as UploadIcon, 
  FileText, 
  X, 
  CheckCircle, 
  AlertCircle,
  Loader2
} from 'lucide-react';
import { documentsAPI } from '../api/documents';
import { toast } from 'react-toastify';
import './Upload.css';

const Upload = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [metadata, setMetadata] = useState({
    title: '',
    document_type: 'contract',
    description: ''
  });

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Upload mutation
  const uploadMutation = useMutation(
    ({ file, metadata }) => documentsAPI.uploadDocument(file, metadata),
    {
      onSuccess: (data) => {
        toast.success('Document uploaded successfully!');
        setUploadedFiles(prev => 
          prev.map(f => 
            f.status === 'uploading' 
              ? { ...f, status: 'completed', id: data.id }
              : f
          )
        );
        queryClient.invalidateQueries('documents');
      },
      onError: (error) => {
        toast.error('Failed to upload document');
        console.error('Upload error:', error);
      },
      onSettled: () => {
        setUploading(false);
        setUploadProgress(0);
      }
    }
  );

  // Handle file selection (not upload)
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length === 0) return;
    
    // Add files to selected files list
    const newFiles = acceptedFiles.map((file, index) => ({
      id: Date.now() + index,
      file,
      name: file.name,
      size: file.size,
      status: 'selected'
    }));
    
    setSelectedFiles(prev => [...prev, ...newFiles]);
  }, []);

  // Handle upload process
  const handleUpload = useCallback(async () => {
    if (selectedFiles.length === 0) {
      toast.error('Please select files to upload');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    for (let i = 0; i < selectedFiles.length; i++) {
      const selectedFile = selectedFiles[i];
      const file = selectedFile.file;
      
      // Add file to uploaded files list
      setUploadedFiles(prev => [...prev, {
        ...selectedFile,
        status: 'uploading',
        progress: 0
      }]);

      try {
        // Simulate progress
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return prev;
            }
            return prev + 10;
          });
        }, 200);

        // Upload file
        await uploadMutation.mutateAsync({
          file,
          metadata: {
            title: metadata.title || file.name.replace(/\.[^/.]+$/, ""),
            document_type: metadata.document_type,
            description: metadata.description
          }
        });

        clearInterval(progressInterval);
        setUploadProgress(100);

      } catch (error) {
        setUploadedFiles(prev => 
          prev.map(f => 
            f.id === selectedFile.id 
              ? { ...f, status: 'error', error: error.message }
              : f
          )
        );
      }
    }

    // Clear selected files after upload
    setSelectedFiles([]);
  }, [selectedFiles, metadata, uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: true
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setMetadata(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const removeSelectedFile = (fileId) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileName) => {
    if (!fileName) return <FileText size={20} className="file-icon" />;
    return <FileText size={20} className="file-icon" />;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={16} className="status-icon success" />;
      case 'error':
        return <AlertCircle size={16} className="status-icon error" />;
      case 'uploading':
        return <Loader2 size={16} className="status-icon uploading" />;
      default:
        return null;
    }
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        <div className="upload-header">
          <h1 className="upload-title">Upload Documents</h1>
          <p className="upload-subtitle">
            Upload your legal documents for AI analysis and processing
          </p>
        </div>

        {/* Upload Form */}
        <div className="upload-form">
          <div className="form-section">
            <label className="form-label">Document Title</label>
            <input
              type="text"
              name="title"
              value={metadata.title}
              onChange={handleInputChange}
              placeholder="Enter document title (optional)"
              className="form-input"
            />
          </div>

          <div className="form-section">
            <label className="form-label">Document Type</label>
            <select
              name="document_type"
              value={metadata.document_type}
              onChange={handleInputChange}
              className="form-select"
            >
              <option value="contract">Contract</option>
              <option value="agreement">Agreement</option>
              <option value="terms">Terms & Conditions</option>
              <option value="policy">Policy</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="form-section">
            <label className="form-label">Description</label>
            <textarea
              name="description"
              value={metadata.description}
              onChange={handleInputChange}
              placeholder="Enter document description (optional)"
              className="form-textarea"
              rows="3"
            />
          </div>
        </div>

        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'dropzone-active' : ''} ${uploading ? 'dropzone-disabled' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="dropzone-content">
            <UploadIcon size={48} className="dropzone-icon" />
            <h3 className="dropzone-title">
              {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
            </h3>
            <p className="dropzone-subtitle">
              or click to select files
            </p>
            <p className="dropzone-info">
              Supports PDF, DOC, DOCX files up to 10MB
            </p>
          </div>
        </div>

        {/* Selected Files */}
        {selectedFiles.length > 0 && (
          <div className="selected-files">
            <h3 className="files-title">Selected Files</h3>
            <div className="files-list">
              {selectedFiles.map((file) => (
                <div key={file.id} className="file-item">
                  <div className="file-info">
                    {getFileIcon(file.name)}
                    <div className="file-details">
                      <span className="file-name">{file.name || 'Unknown file'}</span>
                      <span className="file-size">{formatFileSize(file.size || 0)}</span>
                    </div>
                  </div>
                  
                  <div className="file-status">
                    <span className="status-text selected">Ready to upload</span>
                  </div>

                  <button
                    onClick={() => removeSelectedFile(file.id)}
                    className="remove-btn"
                    title="Remove file"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
            
            {/* Upload Button */}
            <div className="upload-button-container">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="btn btn-primary btn-upload"
              >
                {uploading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <UploadIcon size={16} />
                    Upload Documents
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Upload Progress */}
        {uploading && (
          <div className="upload-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="progress-text">Uploading... {uploadProgress}%</p>
          </div>
        )}

        {/* Uploaded Files List */}
        {uploadedFiles.length > 0 && (
          <div className="uploaded-files">
            <h3 className="files-title">Uploaded Files</h3>
            <div className="files-list">
              {uploadedFiles.map((file) => (
                <div key={file.id} className="file-item uploaded-file-item">
                  <div className="file-info">
                    {getFileIcon(file.name)}
                    <div className="file-details">
                      <span className="file-name">{file.name || 'Unknown file'}</span>
                      <span className="file-size">{formatFileSize(file.size || 0)}</span>
                    </div>
                  </div>
                  
                  <div className="file-status">
                    {getStatusIcon(file.status)}
                    <span className={`status-text ${file.status}`}>
                      {file.status === 'uploading' ? 'Uploading...' : 
                       file.status === 'completed' ? 'Completed' : 
                       file.status === 'error' ? 'Failed' : ''}
                    </span>
                  </div>

                  {/* Document Context/Content */}
                  {file.status === 'completed' && file.title && (
                    <div className="document-context">
                      <div className="context-item">
                        <strong>Title:</strong> {file.title}
                      </div>
                      {file.document_type && (
                        <div className="context-item">
                          <strong>Type:</strong> {file.document_type.charAt(0).toUpperCase() + file.document_type.slice(1)}
                        </div>
                      )}
                      {file.word_count && (
                        <div className="context-item">
                          <strong>Words:</strong> {file.word_count.toLocaleString()}
                        </div>
                      )}
                      {file.character_count && (
                        <div className="context-item">
                          <strong>Characters:</strong> {file.character_count.toLocaleString()}
                        </div>
                      )}
                      {file.parties && file.parties.length > 0 && (
                        <div className="context-item">
                          <strong>Parties:</strong> {file.parties.join(', ')}
                        </div>
                      )}
                      {file.effective_date && (
                        <div className="context-item">
                          <strong>Effective Date:</strong> {new Date(file.effective_date).toLocaleDateString()}
                        </div>
                      )}
                      {file.expiration_date && (
                        <div className="context-item">
                          <strong>Expiration Date:</strong> {new Date(file.expiration_date).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  )}

                  {file.status !== 'uploading' && (
                    <button
                      onClick={() => removeFile(file.id)}
                      className="remove-btn"
                      title="Remove file"
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="upload-actions">
          <button
            onClick={() => navigate('/documents')}
            className="btn btn-outline"
          >
            Back to Documents
          </button>
          
          {uploadedFiles.length > 0 && (
            <button
              onClick={() => navigate('/documents')}
              className="btn btn-primary"
            >
              View Documents
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Upload;
