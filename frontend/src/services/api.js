import { STORAGE_KEYS, API_BASE_URL } from '../utils/constants';

/**
 * Fetch wrapper with authorization headers and JSON handling.
 */
class ApiClient {
  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  getToken() {
    return localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const token = this.getToken();

    const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;

    const headers = {
      Accept: 'application/json, */*',
      ...options.headers,
    };

    if (!isFormData && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    } else if (isFormData) {
      delete headers['Content-Type'];
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      // Handle 401 Unauthorized token expiry
      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
        localStorage.removeItem(STORAGE_KEYS.USER_DATA);
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        }
      }

      if (options.responseType === 'blob') {
        if (!response.ok) {
          const errorText = await response.text().catch(() => '');
          throw new Error(errorText || `Download failed with status ${response.status}`);
        }
        return await response.blob();
      }

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        let errorMessage = `Request failed with status ${response.status}`;
        if (data?.detail) {
          if (Array.isArray(data.detail)) {
            errorMessage = data.detail.map((err) => err.msg || JSON.stringify(err)).join(', ');
          } else if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else {
            errorMessage = JSON.stringify(data.detail);
          }
        } else if (data?.message) {
          errorMessage = data.message;
        }
        const error = new Error(errorMessage);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (error) {
      throw error;
    }
  }

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  post(endpoint, body, options = {}) {
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: isFormData ? body : (typeof body === 'string' ? body : JSON.stringify(body)),
    });
  }

  put(endpoint, body, options = {}) {
    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: isFormData ? body : (typeof body === 'string' ? body : JSON.stringify(body)),
    });
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }

}

export const api = new ApiClient();
export default api;
