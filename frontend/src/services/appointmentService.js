import api from './api';

export const appointmentService = {
  async createAppointment(data) {
    return await api.post('/appointments', data);
  },

  async getMyPatientAppointments(status = '') {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return await api.get(`/appointments/my${query}`);
  },

  async cancelAppointment(appointmentId, cancellationReason = '') {
    const body = cancellationReason ? { cancellation_reason: cancellationReason } : {};
    return await api.patch(`/appointments/${appointmentId}/cancel`, body);
  },

  async getMyDoctorAppointments(status = '') {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return await api.get(`/appointments/doctor/my${query}`);
  },

  async confirmAppointment(appointmentId) {
    return await api.patch(`/appointments/${appointmentId}/confirm`, {});
  },

  async rejectAppointment(appointmentId, rejectionReason = '') {
    const body = rejectionReason ? { rejection_reason: rejectionReason } : {};
    return await api.patch(`/appointments/${appointmentId}/reject`, body);
  },

  async completeAppointment(appointmentId, doctorNotes = '') {
    const body = doctorNotes ? { doctor_notes: doctorNotes } : {};
    return await api.patch(`/appointments/${appointmentId}/complete`, body);
  },

  async getAllAppointments(status = '') {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return await api.get(`/appointments/admin/all${query}`);
  },

  async getAppointmentById(appointmentId) {
    return await api.get(`/appointments/${appointmentId}`);
  },
};

export default appointmentService;
