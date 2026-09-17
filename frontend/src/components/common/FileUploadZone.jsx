import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, Image as ImageIcon, X, AlertCircle } from 'lucide-react';

export default function FileUploadZone({
  onFileSelected,
  selectedFile = null,
  onClear = null,
  disabled = false,
  accept = '.pdf,.jpg,.jpeg,.png',
  maxSizeBytes = 10 * 1024 * 1024,
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const validateAndSelect = (file) => {
    setError(null);
    if (!file) return;

    if (file.size > maxSizeBytes) {
      const mb = (maxSizeBytes / (1024 * 1024)).toFixed(0);
      setError(`File size exceeds maximum limit of ${mb}MB.`);
      return;
    }

    const nameLower = file.name.toLowerCase();
    const validExtensions = ['.pdf', '.jpg', '.jpeg', '.png'];
    const hasValidExt = validExtensions.some((ext) => nameLower.endsWith(ext));
    if (!hasValidExt) {
      setError('Invalid format. Please upload a PDF, JPG, JPEG, or PNG file.');
      return;
    }

    if (onFileSelected) {
      onFileSelected(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelect(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSelect(e.target.files[0]);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const isPdf = selectedFile?.name?.toLowerCase().endsWith('.pdf');

  return (
    <div className="file-upload-zone-wrapper">
      {!selectedFile ? (
        <div
          className={`file-upload-dropzone ${isDragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !disabled && fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              fileInputRef.current?.click();
            }
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={accept}
            onChange={handleInputChange}
            style={{ display: 'none' }}
            disabled={disabled}
          />
          <div className="upload-dropzone-content">
            <div className="upload-icon-circle">
              <UploadCloud size={28} className="text-primary" />
            </div>
            <p className="upload-primary-text">
              <strong>Click to upload</strong> or drag and drop prescription file
            </p>
            <p className="upload-secondary-text">
              Supports PDF, JPG, JPEG, PNG (max 10MB)
            </p>
          </div>
        </div>
      ) : (
        <div className="selected-file-card">
          <div className="selected-file-info">
            <div className="file-icon-badge">
              {isPdf ? <FileText size={22} className="text-danger" /> : <ImageIcon size={22} className="text-info" />}
            </div>
            <div className="file-meta">
              <span className="file-name" title={selectedFile.name}>{selectedFile.name}</span>
              <span className="file-size">{formatFileSize(selectedFile.size)}</span>
            </div>
          </div>
          {onClear && !disabled && (
            <button
              type="button"
              className="btn-clear-file"
              onClick={(e) => {
                e.stopPropagation();
                if (fileInputRef.current) fileInputRef.current.value = '';
                onClear();
              }}
              title="Remove file"
            >
              <X size={18} />
            </button>
          )}
        </div>
      )}

      {error && (
        <div className="upload-error-banner">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
