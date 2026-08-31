import api from './api';

export const dashboardService = {
  /**
   * Fetch authenticated patient's real-time aggregated dashboard.
   */
  async getPatientDashboard() {
    return await api.get('/dashboard/patient');
  },

  /**
   * Fetch authenticated doctor's operational clinical dashboard.
   */
  async getDoctorDashboard() {
    return await api.get('/dashboard/doctor');
  },

  /**
   * Fetch system-wide platform statistics and oversight analytics for admins.
   */
  async getAdminDashboard() {
    return await api.get('/dashboard/admin');
  },

  /**
   * Fetch lab technician clinical testing workspace.
   */
  async getLabTechnicianDashboard() {
    return await api.get('/dashboard/lab-technician');
  },

  /**
   * Fetch pharmacy staff dispensation workspace.
   */
  async getPharmacyDashboard() {
    return await api.get('/dashboard/pharmacy');
  },
};

export default dashboardService;
