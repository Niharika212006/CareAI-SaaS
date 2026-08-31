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
};

export default dashboardService;
