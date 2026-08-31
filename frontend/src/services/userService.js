import api from './api';

export const userService = {
  async getProfile() {
    return await api.get('/users/profile');
  },

  async updateProfile(data) {
    return await api.put('/users/profile', data);
  },
};

export default userService;
