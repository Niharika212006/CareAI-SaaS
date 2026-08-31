import {
  FileText,
  UploadCloud,
  Download,
  ExternalLink,
  Trash2,
  Edit2,
  Search,
  Filter,
  CheckCircle,
  AlertCircle,
  Clock,
  Shield,
  FileSpreadsheet,
  Image as ImageIcon,
  FolderOpen,
  X,
  Save,
  Sparkles,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import medicalDocumentService from '../../services/medicalDocumentService';
import { DocumentAnalysisModal } from '../../components/patient/DocumentAnalysisModal';
import { formatDateTime } from '../../utils/formatters';

const DOCUMENT_TYPES = [
  { id: 'ALL', label: 'All Records' },
  { id: 'LAB_REPORT', label: 'Lab Reports' },
  { id: 'IMAGING', label: 'Imaging / Scans' },
  { id: 'PRESCRIPTION', label: 'Prescriptions' },
  { id: 'DISCHARGE_SUMMARY', label: 'Discharge Summaries' },
  { id: 'MEDICAL_CERTIFICATE', label: 'Certificates' },
  { id: 'OTHER', label: 'Other Docs' },
];

export function PatientMedicalDocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedType, setSelectedType] = useState('ALL');
  const [successMessage, setSuccessMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Upload Form State
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDocType, setUploadDocType] = useState('LAB_REPORT');
  const [uploadDescription, setUploadDescription] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Edit Modal State
  const [editingDoc, setEditingDoc] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDocType, setEditDocType] = useState('OTHER');
  const [editDescription, setEditDescription] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  // Delete Confirmation State
  const [deletingDocId, setDeletingDocId] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // AI Analysis State
  const [selectedDocForAnalysis, setSelectedDocForAnalysis] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [analyzingDocId, setAnalyzingDocId] = useState(null);
  const [analysisModalOpen, setAnalysisModalOpen] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);

  useEffect(() => {
    loadDocuments();
  }, [selectedType]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setErrorMessage(null);
      const params = { limit: 50 };
      if (selectedType !== 'ALL') {
        params.document_type = selectedType;
      }
      const data = await medicalDocumentService.getMyDocuments(params);
      setDocuments(data.items || []);
      setTotalCount(data.total || 0);
    } catch (err) {
      console.error('Failed to load documents:', err);
      setErrorMessage(err.message || 'Failed to load medical documents.');
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleSelectedFile(e.target.files[0]);
    }
  };

  const handleSelectedFile = (file) => {
    const validExtensions = ['.pdf', '.jpg', '.jpeg', '.png'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!validExtensions.includes(ext)) {
      setErrorMessage('Invalid file format. Please upload PDF, JPG, JPEG, or PNG files.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage('File exceeds the 10 MB maximum limit.');
      return;
    }

    setUploadFile(file);
    setErrorMessage(null);
    if (!uploadTitle) {
      // Pre-fill title without extension
      const defaultName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
      setUploadTitle(defaultName.replace(/[\-_]/g, ' '));
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      setErrorMessage('Please select a file to upload.');
      return;
    }
    if (!uploadTitle.trim()) {
      setErrorMessage('Please provide a document title.');
      return;
    }

    try {
      setUploading(true);
      setErrorMessage(null);
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('title', uploadTitle.trim());
      formData.append('document_type', uploadDocType);
      if (uploadDescription.trim()) {
        formData.append('description', uploadDescription.trim());
      }

      await medicalDocumentService.uploadDocument(formData);
      setSuccessMessage(`Document "${uploadTitle.trim()}" uploaded successfully.`);
      setTimeout(() => setSuccessMessage(null), 4000);

      // Reset form
      setUploadFile(null);
      setUploadTitle('');
      setUploadDocType('LAB_REPORT');
      setUploadDescription('');
      if (fileInputRef.current) fileInputRef.current.value = '';

      loadDocuments();
    } catch (err) {
      console.error('Upload failed:', err);
      setErrorMessage(err.message || 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  const openEditModal = (doc) => {
    setEditingDoc(doc);
    setEditTitle(doc.title);
    setEditDocType(doc.document_type);
    setEditDescription(doc.description || '');
  };

  const handleSaveEdit = async () => {
    if (!editTitle.trim()) return;
    try {
      setSavingEdit(true);
      await medicalDocumentService.updateDocument(editingDoc.id, {
        title: editTitle.trim(),
        document_type: editDocType,
        description: editDescription.trim() || null,
      });
      setSuccessMessage('Document metadata updated successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);
      setEditingDoc(null);
      loadDocuments();
    } catch (err) {
      console.error('Update failed:', err);
      setErrorMessage(err.message || 'Failed to update document metadata.');
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingDocId) return;
    try {
      setDeleting(true);
      await medicalDocumentService.deleteDocument(deletingDocId);
      setSuccessMessage('Document deleted successfully.');
      setTimeout(() => setSuccessMessage(null), 3000);
      setDeletingDocId(null);
      loadDocuments();
    } catch (err) {
      console.error('Delete failed:', err);
      setErrorMessage(err.message || 'Failed to delete document.');
    } finally {
      setDeleting(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleAnalyzeDocument = async (doc) => {
    setSelectedDocForAnalysis(doc);
    setAnalysisModalOpen(true);
    setAnalysisLoading(true);
    setAnalysisError(null);
    setAnalyzingDocId(doc.id);
    try {
      const result = await medicalDocumentService.analyzeDocument(doc.id);
      setAnalysisData(result);
    } catch (err) {
      console.error('Document analysis error:', err);
      const msg = err.response?.data?.detail || err.message || 'AI document analysis failed.';
      setAnalysisError(msg);
    } finally {
      setAnalysisLoading(false);
      setAnalyzingDocId(null);
    }
  };

  const getTypeBadge = (type) => {
    switch (type) {
      case 'LAB_REPORT':
        return <Badge variant="blue">Lab Report</Badge>;
      case 'IMAGING':
        return <Badge variant="purple">Imaging / Scan</Badge>;
      case 'PRESCRIPTION':
        return <Badge variant="teal">Prescription</Badge>;
      case 'DISCHARGE_SUMMARY':
        return <Badge variant="amber">Discharge Summary</Badge>;
      case 'MEDICAL_CERTIFICATE':
        return <Badge variant="green">Certificate</Badge>;
      default:
        return <Badge variant="slate">Other</Badge>;
    }
  };

  const getFileIcon = (mimeType) => {
    if (mimeType && mimeType.startsWith('image/')) {
      return <ImageIcon size={22} color="var(--primary-600)" />;
    }
    return <FileText size={22} color="var(--primary-600)" />;
  };

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
          <h1 style={{ fontSize: '1.875rem' }}>Medical Documents & Records</h1>
          <Badge variant="teal">{totalCount} Stored</Badge>
        </div>
        <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
          Securely store, organize, and access your lab test reports, imaging scans, discharge summaries, and medical records.
        </p>
      </div>

      {/* Alerts */}
      {successMessage && (
        <div
          style={{
            background: '#dcfce7',
            border: '1px solid #bbf7d0',
            color: '#15803d',
            padding: '0.875rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
          }}
        >
          <CheckCircle size={18} />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div
          style={{
            background: '#fee2e2',
            border: '1px solid #fecaca',
            color: '#b91c1c',
            padding: '0.875rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
          }}
        >
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Grid Layout: Upload Form (Left) & Document List (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 380px) 1fr', gap: '1.75rem', alignItems: 'start' }}>
        {/* Upload Form Card */}
        <Card title="Upload Health Record" subtitle="PDF, JPG, PNG up to 10MB">
          <form onSubmit={handleUploadSubmit}>
            {/* Drag & Drop Zone */}
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
              style={{
                border: dragActive ? '2px dashed var(--primary-600)' : '2px dashed var(--secondary-300)',
                backgroundColor: dragActive ? 'var(--primary-50)' : '#f8fafc',
                borderRadius: 'var(--radius-md)',
                padding: '1.75rem 1rem',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                marginBottom: '1.25rem',
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <UploadCloud size={36} color="var(--primary-600)" style={{ margin: '0 auto 0.5rem auto' }} />
              {uploadFile ? (
                <div>
                  <div style={{ fontWeight: 700, color: 'var(--secondary-900)', fontSize: '0.875rem' }}>
                    {uploadFile.name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', marginTop: '2px' }}>
                    {formatFileSize(uploadFile.size)} • Click to change file
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--secondary-800)', fontSize: '0.875rem' }}>
                    Click to browse or drag & drop
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', marginTop: '2px' }}>
                    Supports PDF, JPG, PNG (Max 10MB)
                  </div>
                </div>
              )}
            </div>

            {/* Document Title */}
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label className="form-label" style={{ fontSize: '0.8125rem' }}>
                Document Title *
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., Lipid Panel Report"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                required
              />
            </div>

            {/* Document Category */}
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label className="form-label" style={{ fontSize: '0.8125rem' }}>
                Category *
              </label>
              <select
                className="form-input"
                value={uploadDocType}
                onChange={(e) => setUploadDocType(e.target.value)}
              >
                <option value="LAB_REPORT">Lab Report</option>
                <option value="IMAGING">Imaging / Scan (X-Ray, MRI, CT)</option>
                <option value="PRESCRIPTION">Previous Prescription</option>
                <option value="DISCHARGE_SUMMARY">Discharge Summary</option>
                <option value="MEDICAL_CERTIFICATE">Medical Certificate</option>
                <option value="OTHER">Other Health Document</option>
              </select>
            </div>

            {/* Notes / Description */}
            <div className="form-group" style={{ marginBottom: '1.25rem' }}>
              <label className="form-label" style={{ fontSize: '0.8125rem' }}>
                Clinical Notes / Description (Optional)
              </label>
              <textarea
                className="form-input"
                rows={3}
                placeholder="e.g., Fasting blood test conducted at Quest Diagnostics"
                value={uploadDescription}
                onChange={(e) => setUploadDescription(e.target.value)}
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              style={{ width: '100%' }}
              loading={uploading}
              icon={UploadCloud}
              disabled={!uploadFile || !uploadTitle.trim()}
            >
              {uploading ? 'Uploading Record...' : 'Upload Medical Document'}
            </Button>
          </form>
        </Card>

        {/* Document Explorer & Repository (Right) */}
        <div>
          {/* Category Filter Tabs */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
            {DOCUMENT_TYPES.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedType(tab.id)}
                style={{
                  padding: '0.35rem 0.75rem',
                  borderRadius: '6px',
                  border: selectedType === tab.id ? '1px solid var(--primary-600)' : '1px solid var(--secondary-200)',
                  background: selectedType === tab.id ? 'var(--primary-50)' : '#ffffff',
                  color: selectedType === tab.id ? 'var(--primary-800)' : 'var(--secondary-600)',
                  fontWeight: selectedType === tab.id ? 700 : 500,
                  fontSize: '0.8125rem',
                  cursor: 'pointer',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <Card>
            {loading ? (
              <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
                Loading medical records...
              </div>
            ) : documents.length === 0 ? (
              <div style={{ padding: '3.5rem 1rem', textAlign: 'center', background: '#f8fafc', borderRadius: '8px', border: '1px dashed var(--secondary-200)' }}>
                <FolderOpen size={40} color="var(--secondary-400)" style={{ margin: '0 auto 0.75rem auto' }} />
                <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--secondary-800)', marginBottom: '0.25rem' }}>
                  No Medical Documents Found
                </div>
                <p style={{ color: 'var(--secondary-500)', fontSize: '0.875rem', maxWidth: '380px', margin: '0 auto' }}>
                  Upload your lab results, imaging scans, and prescriptions using the upload tool on the left.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    style={{
                      padding: '1.125rem 1.25rem',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--secondary-200)',
                      backgroundColor: '#ffffff',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      gap: '1rem',
                      transition: 'box-shadow 0.15s ease',
                    }}
                  >
                    {/* Document Info */}
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', flex: 1 }}>
                      <div
                        style={{
                          width: '42px',
                          height: '42px',
                          borderRadius: '8px',
                          backgroundColor: 'var(--primary-50)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                        }}
                      >
                        {getFileIcon(doc.mime_type)}
                      </div>

                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '4px', flexWrap: 'wrap' }}>
                          <strong style={{ fontSize: '0.9375rem', color: 'var(--secondary-900)' }}>
                            {doc.title}
                          </strong>
                          {getTypeBadge(doc.document_type)}
                        </div>

                        {doc.description && (
                          <p style={{ fontSize: '0.8125rem', color: 'var(--secondary-600)', margin: '0 0 6px 0', lineHeight: 1.4 }}>
                            {doc.description}
                          </p>
                        )}

                        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: 'var(--secondary-400)', flexWrap: 'wrap' }}>
                          <span><strong>File:</strong> {doc.file_name}</span>
                          <span><strong>Size:</strong> {formatFileSize(doc.file_size)}</span>
                          <span><strong>Uploaded:</strong> {formatDateTime(doc.created_at)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <button
                        onClick={() => handleAnalyzeDocument(doc)}
                        title="Analyze Document with AI"
                        disabled={analyzingDocId === doc.id}
                        style={{
                          padding: '0.45rem 0.75rem',
                          borderRadius: '6px',
                          border: '1px solid #c7d2fe',
                          background: '#eef2ff',
                          color: '#4338ca',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          transition: 'all 0.15s ease',
                        }}
                      >
                        <Sparkles size={14} color="#4f46e5" />
                        <span>{analyzingDocId === doc.id ? 'Analyzing...' : 'AI Insights'}</span>
                      </button>

                      <button
                        onClick={() => medicalDocumentService.viewDocument(doc.id)}
                        title="View Document"
                        style={{
                          padding: '0.45rem',
                          borderRadius: '6px',
                          border: '1px solid var(--secondary-200)',
                          background: '#ffffff',
                          color: 'var(--secondary-700)',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <ExternalLink size={15} />
                      </button>

                      <button
                        onClick={() => medicalDocumentService.downloadDocument(doc.id, doc.file_name)}
                        title="Download Document"
                        style={{
                          padding: '0.45rem',
                          borderRadius: '6px',
                          border: '1px solid var(--secondary-200)',
                          background: '#ffffff',
                          color: 'var(--primary-600)',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <Download size={15} />
                      </button>

                      <button
                        onClick={() => openEditModal(doc)}
                        title="Edit Metadata"
                        style={{
                          padding: '0.45rem',
                          borderRadius: '6px',
                          border: '1px solid var(--secondary-200)',
                          background: '#ffffff',
                          color: 'var(--secondary-700)',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <Edit2 size={15} />
                      </button>

                      <button
                        onClick={() => setDeletingDocId(doc.id)}
                        title="Delete Document"
                        style={{
                          padding: '0.45rem',
                          borderRadius: '6px',
                          border: '1px solid var(--secondary-200)',
                          background: '#ffffff',
                          color: 'var(--accent-rose)',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Edit Metadata Modal */}
      {editingDoc && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '480px',
              width: '100%',
              padding: '1.5rem',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.125rem', margin: 0 }}>Edit Document Details</h3>
              <button
                onClick={() => setEditingDoc(null)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--secondary-400)' }}
              >
                <X size={20} />
              </button>
            </div>

            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label className="form-label">Document Title</label>
              <input
                type="text"
                className="form-input"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label className="form-label">Category</label>
              <select
                className="form-input"
                value={editDocType}
                onChange={(e) => setEditDocType(e.target.value)}
              >
                <option value="LAB_REPORT">Lab Report</option>
                <option value="IMAGING">Imaging / Scan</option>
                <option value="PRESCRIPTION">Prescription</option>
                <option value="DISCHARGE_SUMMARY">Discharge Summary</option>
                <option value="MEDICAL_CERTIFICATE">Medical Certificate</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
              <label className="form-label">Description / Notes</label>
              <textarea
                className="form-input"
                rows={3}
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="secondary" onClick={() => setEditingDoc(null)}>
                Cancel
              </Button>
              <Button variant="primary" icon={Save} loading={savingEdit} onClick={handleSaveEdit}>
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingDocId && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '420px',
              width: '100%',
              padding: '1.5rem',
              textAlign: 'center',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
            }}
          >
            <AlertCircle size={44} color="var(--accent-rose)" style={{ margin: '0 auto 0.75rem auto' }} />
            <h3 style={{ fontSize: '1.125rem', marginBottom: '0.5rem' }}>Delete Medical Document?</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--secondary-600)', marginBottom: '1.5rem' }}>
              This will permanently delete this document and its stored file. This action cannot be undone.
            </p>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem' }}>
              <Button variant="secondary" onClick={() => setDeletingDocId(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                style={{ backgroundColor: 'var(--accent-rose)', borderColor: 'var(--accent-rose)' }}
                loading={deleting}
                onClick={handleDelete}
              >
                Yes, Delete
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* AI Document Analysis Modal */}
      <DocumentAnalysisModal
        isOpen={analysisModalOpen}
        onClose={() => {
          setAnalysisModalOpen(false);
          setAnalysisData(null);
          setAnalysisError(null);
        }}
        analysis={analysisData}
        document={selectedDocForAnalysis}
        isLoading={analysisLoading}
        error={analysisError}
        onRetry={() => selectedDocForAnalysis && handleAnalyzeDocument(selectedDocForAnalysis)}
      />
    </div>
  );
}

export default PatientMedicalDocumentsPage;
