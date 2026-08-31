import api from './api';

export const aiService = {
  /**
   * Run multi-vector clinical safety analysis on a specific prescription.
   */
  async analyzePrescription(prescriptionId) {
    return await api.post(`/ai/prescriptions/${prescriptionId}/analyze`);
  },

  /**
   * Retrieve the latest AI safety report for a prescription.
   */
  async getPrescriptionReport(prescriptionId) {
    return await api.get(`/ai/prescriptions/${prescriptionId}/report`);
  },

  /**
   * Retrieve all historical AI safety reports for the authenticated patient.
   */
  async getMyReports(skip = 0, limit = 50) {
    return await api.get(`/ai/reports/my?skip=${skip}&limit=${limit}`);
  },

  /**
   * Ad-hoc interaction check for arbitrary medication lists.
   */
  async analyzeInteractions(payload) {
    return await api.post('/ai/analyze-interactions', payload);
  },
};

export default aiService;
