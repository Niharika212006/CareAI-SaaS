import api from './api';

export const userService = {
  async getProfile() {
    return await api.get('/users/profile');
  },

  async updateProfile(data) {
    return await api.put('/users/profile', data);
  },
};

export const doctorService = {
  async getDirectory(specialization = '') {
    const query = specialization ? `?specialization=${encodeURIComponent(specialization)}` : '';
    return await api.get(`/doctors/directory${query}`);
  },

  async getMyProfile() {
    return await api.get('/doctors/me/profile');
  },

  async updateMyProfile(data) {
    return await api.put('/doctors/me/profile', data);
  },

  async getPendingDoctors() {
    return await api.get('/admin/pending-doctors');
  },

  async reviewDoctor(doctorId, approvalData) {
    return await api.put(`/admin/doctors/${doctorId}/approval`, approvalData);
  },
};

export const patientService = {
  async getMyProfile() {
    return await api.get('/patients/me/profile');
  },

  async updateMyProfile(data) {
    return await api.put('/patients/me/profile', data);
  },
};

export const aiService = {
  async analyzeInteractions(payload) {
    return await api.post('/ai/analyze-interactions', payload);
  },
};

export { appointmentService } from './appointmentService';
export { prescriptionService } from './prescriptionService';


