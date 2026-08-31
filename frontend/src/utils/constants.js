/**
 * Application Constants and Enums
 */

export const USER_ROLES = {
  PATIENT: 'PATIENT',
  DOCTOR: 'DOCTOR',
  ADMIN: 'ADMIN',
  LAB_TECHNICIAN: 'LAB_TECHNICIAN',
  PHARMACY_STAFF: 'PHARMACY_STAFF',
};

export const DOCTOR_APPROVAL_STATUS = {
  PENDING: 'PENDING',
  APPROVED: 'APPROVED',
  REJECTED: 'REJECTED',
};

export const APPOINTMENT_STATUS = {
  PENDING: 'PENDING',
  CONFIRMED: 'CONFIRMED',
  CANCELLED: 'CANCELLED',
  COMPLETED: 'COMPLETED',
  REJECTED: 'REJECTED',
};

export const INTERACTION_SEVERITY = {
  NONE: 'NONE',
  LOW: 'LOW',
  MODERATE: 'MODERATE',
  HIGH: 'HIGH',
  CRITICAL: 'CRITICAL',
};

const rawApiUrl =
  (typeof import.meta !== 'undefined' &&
    import.meta.env &&
    (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL)) ||
  '';

export const API_BASE_URL = (() => {
  if (rawApiUrl) {
    const trimmed = rawApiUrl.trim().replace(/\/+$/, '');
    return trimmed.endsWith('/api/v1') ? trimmed : `${trimmed}/api/v1`;
  }
  if (
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') &&
    window.location.port === '5173'
  ) {
    return 'http://127.0.0.1:8000/api/v1';
  }
  return '/api/v1';
})();

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'healthcare_auth_token',
  USER_DATA: 'healthcare_user_data',
};
