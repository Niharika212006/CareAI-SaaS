import api from './api';

export const prescriptionService = {
  async createPrescription(data) {
    return await api.post('/prescriptions', data);
  },

  async getMyDoctorPrescriptions(skip = 0, limit = 50) {
    return await api.get(`/prescriptions/doctor/my?skip=${skip}&limit=${limit}`);
  },

  async getMyPatientPrescriptions(skip = 0, limit = 50) {
    return await api.get(`/prescriptions/my?skip=${skip}&limit=${limit}`);
  },

  async getPrescriptionById(prescriptionId) {
    return await api.get(`/prescriptions/${prescriptionId}`);
  },

  async getPrescriptionByAppointment(appointmentId) {
    return await api.get(`/prescriptions/appointment/${appointmentId}`);
  },
};

export default prescriptionService;
