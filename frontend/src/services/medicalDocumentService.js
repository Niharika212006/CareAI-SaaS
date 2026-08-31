import api from './api';

export const medicalDocumentService = {
  /**
   * Upload a medical document for the current patient.
   */
  async uploadDocument(formData) {
    return await api.post('/medical-documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * List medical documents for current authenticated patient.
   */
  async getMyDocuments(params = {}) {
    const query = new URLSearchParams();
    if (params.document_type) query.append('document_type', params.document_type);
    if (params.skip !== undefined) query.append('skip', params.skip);
    if (params.limit !== undefined) query.append('limit', params.limit);

    const qs = query.toString();
    const endpoint = `/medical-documents${qs ? `?${qs}` : ''}`;
    return await api.get(endpoint);
  },

  /**
   * Get document metadata.
   */
  async getDocumentMetadata(documentId) {
    return await api.get(`/medical-documents/${documentId}`);
  },

  /**
   * Download physical document file as Blob.
   */
  async downloadDocument(documentId, fileName = 'medical_document') {
    const response = await api.get(`/medical-documents/${documentId}/download`, {
      responseType: 'blob',
    });
    
    // Trigger browser download
    const url = window.URL.createObjectURL(new Blob([response]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  /**
   * View document in a new browser tab.
   */
  async viewDocument(documentId) {
    const response = await api.get(`/medical-documents/${documentId}/download`, {
      responseType: 'blob',
    });
    const file = new Blob([response], { type: response.type || 'application/pdf' });
    const fileURL = URL.createObjectURL(file);
    window.open(fileURL, '_blank');
  },

  /**
   * Update document metadata (title, category, description).
   */
  async updateDocument(documentId, data) {
    return await api.patch(`/medical-documents/${documentId}`, data);
  },

  /**
   * Delete document by ID.
   */
  async deleteDocument(documentId) {
    return await api.delete(`/medical-documents/${documentId}`);
  },

  /**
   * Doctor access: list medical documents for an authorized patient.
   */
  async getPatientDocumentsForDoctor(patientId, params = {}) {
    const query = new URLSearchParams();
    if (params.document_type) query.append('document_type', params.document_type);
    if (params.skip !== undefined) query.append('skip', params.skip);
    if (params.limit !== undefined) query.append('limit', params.limit);

    const qs = query.toString();
    const endpoint = `/doctors/patients/${patientId}/medical-documents${qs ? `?${qs}` : ''}`;
    return await api.get(endpoint);
  },

  /**
   * Request AI analysis for an owned medical document.
   */
  async analyzeDocument(documentId) {
    return await api.post(`/medical-documents/${documentId}/analyze`);
  },

  /**
   * Get latest AI analysis for a document.
   */
  async getDocumentAnalysis(documentId) {
    return await api.get(`/medical-documents/${documentId}/analysis`);
  },

  /**
   * Get document analysis by primary ID.
   */
  async getAnalysisById(analysisId) {
    return await api.get(`/document-analyses/${analysisId}`);
  },
};

export default medicalDocumentService;
