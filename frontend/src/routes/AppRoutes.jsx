import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import PublicLayout from '../layouts/PublicLayout';
import AuthLayout from '../layouts/AuthLayout';
import DashboardLayout from '../layouts/DashboardLayout';
import ProtectedRoute from '../components/common/ProtectedRoute';
import { USER_ROLES } from '../utils/constants';

// Public & Auth Pages
import HomePage from '../pages/public/HomePage';
import NotFoundPage from '../pages/public/NotFoundPage';
import LoginPage from '../pages/auth/LoginPage';
import RegisterPage from '../pages/auth/RegisterPage';

// Domain Pages
import DoctorDirectoryPage from '../pages/patient/DoctorDirectoryPage';
import PatientDashboardPage from '../pages/patient/PatientDashboardPage';
import PatientMedicalProfilePage from '../pages/patient/PatientMedicalProfilePage';
import PatientAppointmentsPage from '../pages/patient/PatientAppointmentsPage';
import PatientPrescriptionsPage from '../pages/patient/PatientPrescriptionsPage';
import DoctorDashboardPage from '../pages/doctor/DoctorDashboardPage';
import DoctorAppointmentsPage from '../pages/doctor/DoctorAppointmentsPage';
import DoctorPrescriptionsPage from '../pages/doctor/DoctorPrescriptionsPage';
import DoctorAvailabilityPage from '../pages/doctor/DoctorAvailabilityPage';
import AdminDashboardPage from '../pages/admin/AdminDashboardPage';
import NotificationsPage from '../pages/common/NotificationsPage';
import PatientMedicalDocumentsPage from '../pages/patient/PatientMedicalDocumentsPage';

export function AppRoutes() {
  return (
    <Routes>
      {/* Public Pages */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/doctors" element={<DoctorDirectoryPage />} />
      </Route>

      {/* Authentication Pages */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Top-Level Authenticated Notifications Route */}
      <Route
        path="/notifications"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.PATIENT, USER_ROLES.DOCTOR, USER_ROLES.ADMIN]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<NotificationsPage />} />
      </Route>

      {/* Strict Protected Patient Routes */}
      <Route
        path="/patient"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.PATIENT]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<PatientDashboardPage />} />
        <Route path="profile" element={<PatientMedicalProfilePage />} />
        <Route path="medical-profile" element={<PatientMedicalProfilePage />} />
        <Route path="prescriptions" element={<PatientPrescriptionsPage />} />
        <Route path="appointments" element={<PatientAppointmentsPage />} />
        <Route path="documents" element={<PatientMedicalDocumentsPage />} />
        <Route path="records" element={<PatientMedicalDocumentsPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
      </Route>

      {/* Strict Protected Doctor Routes */}
      <Route
        path="/doctor"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.DOCTOR]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DoctorDashboardPage />} />
        <Route path="profile" element={<DoctorDashboardPage />} />
        <Route path="appointments" element={<DoctorAppointmentsPage />} />
        <Route path="prescriptions" element={<DoctorPrescriptionsPage />} />
        <Route path="availability" element={<DoctorAvailabilityPage />} />
        <Route path="schedule" element={<DoctorAvailabilityPage />} />
        <Route path="ai-analyzer" element={<DoctorDashboardPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
      </Route>

      {/* Strict Protected Admin Routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={[USER_ROLES.ADMIN]}>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboardPage />} />
        <Route path="doctors" element={<AdminDashboardPage />} />
        <Route path="users" element={<AdminDashboardPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
      </Route>

      {/* Fallback 404 Route */}
      <Route element={<PublicLayout />}>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default AppRoutes;
