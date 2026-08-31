import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Calendar,
  FileText,
  UserCheck,
  Users,
  Search,
  Sparkles,
  Settings,
  ShieldAlert,
  Clock,
  Bell,
  FolderOpen,
} from 'lucide-react';
import useAuth from '../../hooks/useAuth';

export function Sidebar() {
  const { isPatient, isDoctor, isAdmin } = useAuth();

  const patientLinks = [
    { to: '/patient/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/patient/profile', label: 'Health Profile', icon: UserCheck },
    { to: '/patient/documents', label: 'Medical Records', icon: FolderOpen },
    { to: '/patient/prescriptions', label: 'My Prescriptions', icon: FileText },
    { to: '/patient/appointments', label: 'Appointments', icon: Calendar },
    { to: '/doctors', label: 'Find Doctors', icon: Search },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ];

  const doctorLinks = [
    { to: '/doctor/dashboard', label: 'Doctor Dashboard', icon: LayoutDashboard },
    { to: '/doctor/profile', label: 'Clinical Profile', icon: UserCheck },
    { to: '/doctor/appointments', label: 'Patient Consultations', icon: Calendar },
    { to: '/doctor/availability', label: 'Working Schedule', icon: Clock },
    { to: '/doctor/prescriptions', label: 'Prescription Writer', icon: FileText },
    { to: '/doctor/ai-analyzer', label: 'AI Drug Safety', icon: Sparkles },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ];

  const adminLinks = [
    { to: '/admin/dashboard', label: 'Admin Overview', icon: LayoutDashboard },
    { to: '/admin/doctors', label: 'Doctor Verifications', icon: ShieldAlert },
    { to: '/admin/users', label: 'User Directory', icon: Users },
    { to: '/notifications', label: 'Notifications', icon: Bell },
  ];

  let links = patientLinks;
  if (isDoctor) links = doctorLinks;
  if (isAdmin) links = adminLinks;

  return (
    <aside
      style={{
        width: '260px',
        backgroundColor: '#ffffff',
        borderRight: '1px solid var(--secondary-200)',
        display: 'flex',
        flexDirection: 'column',
        padding: '1.5rem 1rem',
      }}
    >
      <div style={{ marginBottom: '1.5rem', paddingLeft: '0.75rem' }}>
        <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--secondary-500)', fontWeight: 700 }}>
          Navigation
        </span>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', flex: 1 }}>
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.625rem 0.875rem',
                borderRadius: 'var(--radius-md)',
                textDecoration: 'none',
                fontSize: '0.875rem',
                fontWeight: 600,
                color: isActive ? 'var(--primary-700)' : 'var(--secondary-700)',
                backgroundColor: isActive ? 'var(--primary-50)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--primary-600)' : '3px solid transparent',
                transition: 'all var(--transition-fast)',
              })}
            >
              <Icon size={18} />
              {link.label}
            </NavLink>
          );
        })}
      </nav>

      <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--secondary-200)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', color: 'var(--secondary-500)', fontSize: '0.75rem' }}>
          <Sparkles size={14} color="var(--primary-600)" />
          <span>AI Clinical Engine Active</span>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
