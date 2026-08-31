import React, { useState, useEffect } from 'react';
import { Pill, Activity, CheckCircle, AlertTriangle, Clock, PackageCheck } from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import useAuth from '../../hooks/useAuth';
import dashboardService from '../../services/dashboardService';

export function PharmacyDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchPharmacyDashboard() {
      try {
        setLoading(true);
        const res = await dashboardService.getPharmacyDashboard();
        setData(res);
      } catch (err) {
        setError(err.message || 'Failed to load Pharmacy Staff workspace.');
      } finally {
        setLoading(false);
      }
    }
    fetchPharmacyDashboard();
  }, []);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #0284c7 0%, #0d9488 100%)',
          color: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          padding: '2rem',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.2)', padding: '0.5rem', borderRadius: '10px' }}>
            <Pill size={24} color="#ffffff" />
          </div>
          <Badge variant="teal" style={{ background: '#ffffff', color: '#0d9488', fontWeight: 700 }}>
            Pharmacy Staff Portal
          </Badge>
        </div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0.25rem 0' }}>
          Welcome, {user?.full_name || 'Pharmacist'}
        </h1>
        <p style={{ color: 'rgba(255, 255, 255, 0.85)', margin: 0, fontSize: '0.9375rem' }}>
          Prescription fulfillment, formulary inventory management, and medication dispensing.
        </p>
      </div>

      {loading ? (
        <Card style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
          <Activity size={28} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#0d9488' }} />
          <div>Loading Pharmacy Workspace...</div>
        </Card>
      ) : error ? (
        <Card style={{ padding: '2rem', background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c' }}>
          <AlertTriangle size={24} style={{ marginBottom: '0.5rem' }} />
          <div style={{ fontWeight: 600 }}>{error}</div>
        </Card>
      ) : (
        <>
          {/* Key Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Pending Pickups</span>
                <Clock size={18} color="#0284c7" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.pending_dispensations ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#0284c7', marginTop: '0.25rem' }}>Awaiting patient fulfillment</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Verified Today</span>
                <CheckCircle size={18} color="#059669" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.prescriptions_verified_today ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#059669', marginTop: '0.25rem' }}>Prescriptions processed</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Stock Alerts</span>
                <AlertTriangle size={18} color="#d97706" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.low_stock_alerts ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#d97706', marginTop: '0.25rem' }}>Items below reorder point</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Total Dispensed</span>
                <PackageCheck size={18} color="#0d9488" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.total_medications_dispensed ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#0d9488', marginTop: '0.25rem' }}>Cumulative platform units</div>
            </Card>
          </div>

          {/* Pending Dispensations Queue */}
          <Card className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>Prescription Fulfillment Queue</h3>
              <Badge variant="teal">Foundation Mode</Badge>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {(data?.pending_dispensations || []).map((disp) => (
                <div
                  key={disp.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.875rem 1rem',
                    background: 'var(--bg-main)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--secondary-200)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ background: '#ccfbf1', padding: '0.5rem', borderRadius: '8px', color: '#0f766e' }}>
                      <Pill size={16} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{disp.medication}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Patient: {disp.patient_name}</div>
                    </div>
                  </div>
                  <Badge variant={disp.status === 'READY_FOR_PICKUP' ? 'green' : 'amber'}>
                    {disp.status.replace(/_/g, ' ')}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

export default PharmacyDashboardPage;
