import api from './api';

/**
 * Service client for Pharmacy Staff workspace, prescription dispensary queue, and safety alerts.
 */
export const pharmacyService = {
  /**
   * Fetch live dashboard operational stats and active queue for pharmacy staff.
   */
  async getDashboard() {
    return await api.get('/pharmacy/dashboard');
  },

  /**
   * List prescriptions in dispensary queue with filters.
   * @param {Object} params - { status, search, risk_level, skip, limit }
   */
  async getPrescriptions(params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.search) query.append('search', params.search);
    if (params.risk_level) query.append('risk_level', params.risk_level);
    if (params.skip !== undefined) query.append('skip', params.skip);
    if (params.limit !== undefined) query.append('limit', params.limit);
    return await api.get(`/pharmacy/prescriptions?${query.toString()}`);
  },

  /**
   * Get full prescription details including medication items and AI safety report.
   * @param {number} prescriptionId
   */
  async getPrescription(prescriptionId) {
    return await api.get(`/pharmacy/prescriptions/${prescriptionId}`);
  },

  /**
   * Update prescription dispensing workflow status.
   * @param {number} prescriptionId
   * @param {Object} data - { status: "UNDER_REVIEW" | "READY" | "DISPENSED" | "CANCELLED", pharmacy_notes: string }
   */
  async updateStatus(prescriptionId, data) {
    return await api.request(`/pharmacy/prescriptions/${prescriptionId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Mark prescription as dispensed with optional pharmacist notes.
   * @param {number} prescriptionId
   * @param {Object} data - { pharmacy_notes: string }
   */
  async dispense(prescriptionId, data = {}) {
    return await api.post(`/pharmacy/prescriptions/${prescriptionId}/dispense`, data);
  },
};

export default pharmacyService;
