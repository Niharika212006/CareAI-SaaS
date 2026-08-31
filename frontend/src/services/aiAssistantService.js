import api from './api';

/**
 * Service client for Centralized Role-Aware CareAI Assistant endpoints.
 */
export const aiAssistantService = {
  /**
   * Send a message turn to the CareAI Assistant.
   * @param {string} message - User query / prompt
   * @param {number|null} conversationId - Optional existing conversation thread ID
   */
  async sendMessage(message, conversationId = null) {
    const payload = {
      message: message.trim(),
    };
    if (conversationId) {
      payload.conversation_id = conversationId;
    }
    return await api.post('/ai-assistant/chat', payload);
  },

  /**
   * Fetch all conversation thread summaries for the authenticated user.
   * @param {number} skip - Offset
   * @param {number} limit - Max items
   */
  async getConversations(skip = 0, limit = 50) {
    return await api.get(`/ai-assistant/conversations?skip=${skip}&limit=${limit}`);
  },

  /**
   * Fetch complete message history for an authorized conversation thread.
   * @param {number} conversationId
   */
  async getConversation(conversationId) {
    return await api.get(`/ai-assistant/conversations/${conversationId}`);
  },

  /**
   * Permanently delete a conversation thread and its associated message history.
   * @param {number} conversationId
   */
  async deleteConversation(conversationId) {
    return await api.delete(`/ai-assistant/conversations/${conversationId}`);
  },
};

export default aiAssistantService;
