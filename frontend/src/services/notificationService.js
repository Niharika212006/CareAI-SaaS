import api from './api';

export const notificationService = {
  /**
   * Retrieve paginated notifications for authenticated user.
   */
  async getNotifications(params = {}) {
    const query = new URLSearchParams();
    if (params.unread_only) query.append('unread_only', 'true');
    if (params.skip !== undefined) query.append('skip', params.skip);
    if (params.limit !== undefined) query.append('limit', params.limit);

    const qs = query.toString();
    const endpoint = `/notifications${qs ? `?${qs}` : ''}`;
    return await api.get(endpoint);
  },

  /**
   * Get unread notification counter for badge.
   */
  async getUnreadCount() {
    return await api.get('/notifications/unread-count');
  },

  /**
   * Mark single notification as read.
   */
  async markAsRead(notificationId) {
    return await api.patch(`/notifications/${notificationId}/read`);
  },

  /**
   * Mark all notifications for authenticated user as read.
   */
  async markAllAsRead() {
    return await api.patch('/notifications/read-all');
  },

  /**
   * Delete a notification from user history.
   */
  async deleteNotification(notificationId) {
    return await api.delete(`/notifications/${notificationId}`);
  },
};

export default notificationService;
