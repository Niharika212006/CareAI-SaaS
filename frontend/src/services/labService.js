import api from './api';

/**
 * Service client for Laboratory Management and Diagnostic Workflows.
 */
export const labService = {
  // --- Catalog (All Roles / Admin) ---
  async getTests(params = {}) {
    const query = new URLSearchParams();
    if (params.category) query.append('category', params.category);
    if (params.search) query.append('search', params.search);
    if (params.active_only !== undefined) query.append('active_only', params.active_only);
    if (params.skip !== undefined) query.append('skip', params.skip);
    if (params.limit !== undefined) query.append('limit', params.limit);
    return await api.get(`/lab/tests?${query.toString()}`);
  },

  async getTest(testId) {
    return await api.get(`/lab/tests/${testId}`);
  },

  async createTest(testData) {
    return await api.post('/lab/tests', testData);
  },

  async updateTest(testId, testData) {
    return await api.put(`/lab/tests/${testId}`, testData);
  },

  async toggleTestStatus(testId, isActive) {
    return await api.request(`/lab/tests/${testId}/status?is_active=${isActive}`, { method: 'PATCH' });
  },

  // --- Doctor Orders ---
  async createOrder(orderData) {
    return await api.post('/lab/orders', orderData);
  },

  async getDoctorOrders(skip = 0, limit = 50) {
    return await api.get(`/lab/orders/my-doctor-orders?skip=${skip}&limit=${limit}`);
  },

  async getOrder(orderId) {
    return await api.get(`/lab/orders/${orderId}`);
  },

  async cancelOrder(orderId, reason = null) {
    const query = reason ? `?reason=${encodeURIComponent(reason)}` : '';
    return await api.post(`/lab/orders/${orderId}/cancel${query}`);
  },

  // --- Lab Technician Queue & Workflows ---
  async getWorkQueue(params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.priority) query.append('priority', params.priority);
    if (params.search) query.append('search', params.search);
    if (params.skip !== undefined) query.append('skip', params.skip);
    if (params.limit !== undefined) query.append('limit', params.limit);
    return await api.get(`/lab/queue?${query.toString()}`);
  },

  async getQueueStats() {
    return await api.get('/lab/stats');
  },

  async getAdminStats() {
    return await api.get('/lab/admin-stats');
  },

  async collectSample(orderId, sampleData) {
    return await api.post(`/lab/orders/${orderId}/collect-sample`, sampleData);
  },

  async startProcessing(orderId) {
    return await api.post(`/lab/orders/${orderId}/start-processing`);
  },

  async enterResults(orderId, batchData) {
    return await api.post(`/lab/orders/${orderId}/enter-results`, batchData);
  },

  async verifyResults(orderId, verificationNotes = null) {
    return await api.post(`/lab/orders/${orderId}/verify`, { verification_notes: verificationNotes });
  },

  async releaseResults(orderId) {
    return await api.post(`/lab/orders/${orderId}/release`);
  },

  // --- Patient Portal ---
  async getPatientReports(skip = 0, limit = 50) {
    return await api.get(`/lab/patient/my-reports?skip=${skip}&limit=${limit}`);
  },

  async getPatientReportDetail(orderId) {
    return await api.get(`/lab/patient/my-reports/${orderId}`);
  },
};

export default labService;
