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

export const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) ||
  (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port === '5173'
    ? 'http://127.0.0.1:8000/api/v1'
    : '/api/v1');

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'healthcare_auth_token',
  USER_DATA: 'healthcare_user_data',
};
