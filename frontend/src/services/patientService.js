import api from './api';

export const patientService = {
  /**
   * Fetch authenticated patient's comprehensive medical profile.
   */
  async getMedicalProfile() {
    return await api.get('/patients/medical-profile');
  },

  /**
   * Update full medical profile (allergies, medications, conditions, emergency info).
   */
  async updateMedicalProfile(data) {
    return await api.put('/patients/medical-profile', data);
  },

  /**
   * Partially update specified fields of patient medical profile.
   */
  async patchMedicalProfile(data) {
    return await api.patch('/patients/medical-profile', data);
  },

  /**
   * Doctor access to treating patient's clinical medical summary.
   */
  async getDoctorPatientSummary(patientId) {
    return await api.get(`/patients/${patientId}/medical-summary`);
  },

  /**
   * Legacy profile fetch.
   */
  async getMyProfile() {
    return await api.get('/patients/me/profile');
  },

  /**
   * Legacy profile update.
   */
  async updateMyProfile(data) {
    return await api.put('/patients/me/profile', data);
  },
};

export default patientService;
