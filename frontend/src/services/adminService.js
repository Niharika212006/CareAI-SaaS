import api from './api';

/**
 * Service client for Administrator platform management, doctor approvals, and staff provisioning.
 */
export const adminService = {
  /**
   * Provision a verified staff account (Lab Technician, Pharmacy Staff, Admin).
   */
  async provisionStaff(staffData) {
    return await api.post('/admin/staff', staffData);
  },

  /**
   * Retrieve list of doctor applications pending administrative approval.
   */
  async getPendingDoctors(skip = 0, limit = 50) {
    return await api.get(`/admin/pending-doctors?skip=${skip}&limit=${limit}`);
  },

  /**
   * Approve or reject doctor credentials with notes.
   */
  async reviewDoctor(doctorId, approvalData) {
    return await api.put(`/admin/doctors/${doctorId}/approval`, approvalData);
  },

  /**
   * Retrieve full audit list of registered platform user accounts.
   */
  async listUsers(skip = 0, limit = 100) {
    return await api.get(`/admin/users?skip=${skip}&limit=${limit}`);
  },
};

export default adminService;
