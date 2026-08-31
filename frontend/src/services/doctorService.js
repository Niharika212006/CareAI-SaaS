import api from './api';

export const doctorService = {
  /**
   * Public discovery of approved doctors.
   */
  async getDirectory(specialization) {
    const params = specialization ? `?specialization=${encodeURIComponent(specialization)}` : '';
    return await api.get(`/doctors/directory${params}`);
  },

  /**
   * Dynamically calculate available appointment slots for a doctor on a specific date.
   */
  async getAvailableSlots(doctorId, dateStr) {
    return await api.get(`/doctors/${doctorId}/available-slots?date=${dateStr}`);
  },

  /**
   * Retrieve authenticated doctor's profile.
   */
  async getMyProfile() {
    return await api.get('/doctors/me/profile');
  },

  /**
   * Update doctor's profile.
   */
  async updateMyProfile(data) {
    return await api.put('/doctors/me/profile', data);
  },

  /**
   * Retrieve doctor's weekly availability schedule rules.
   */
  async getMyAvailability() {
    return await api.get('/doctors/availability/my');
  },

  /**
   * Create a new weekly availability schedule window.
   */
  async createAvailability(data) {
    return await api.post('/doctors/availability', data);
  },

  /**
   * Update an existing availability schedule rule.
   */
  async updateAvailability(availabilityId, data) {
    return await api.put(`/doctors/availability/${availabilityId}`, data);
  },

  /**
   * Delete an availability schedule rule.
   */
  async deleteAvailability(availabilityId) {
    return await api.delete(`/doctors/availability/${availabilityId}`);
  },

  /**
   * Retrieve doctor's recorded unavailable / leave dates.
   */
  async getMyUnavailableDates() {
    return await api.get('/doctors/unavailable-dates/my');
  },

  /**
   * Add a new unavailable / absence date.
   */
  async addUnavailableDate(data) {
    return await api.post('/doctors/unavailable-dates', data);
  },

  /**
   * Retrieve list of doctor applications pending administrative review (Admin).
   */
  async getPendingDoctors(skip = 0, limit = 50) {
    return await api.get(`/admin/pending-doctors?skip=${skip}&limit=${limit}`);
  },

  /**
   * Update doctor application approval status (Admin).
   */
  async reviewDoctor(doctorId, approvalData) {
    return await api.put(`/admin/doctors/${doctorId}/approval`, approvalData);
  },
};

export default doctorService;

