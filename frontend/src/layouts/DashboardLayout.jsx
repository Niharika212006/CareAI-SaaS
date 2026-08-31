import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/common/Navbar';
import Sidebar from '../components/common/Sidebar';
import Footer from '../components/common/Footer';

export function DashboardLayout() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <div className="app-container" style={{ flex: 1 }}>
        <Sidebar />
        <main className="main-content">
          <div className="page-container">
            <Outlet />
          </div>
          <Footer />
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;
