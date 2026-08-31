import React, { useState, useEffect } from 'react';
import { FlaskConical, Activity, CheckCircle, AlertTriangle, Clock, Sparkles } from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import useAuth from '../../hooks/useAuth';
import dashboardService from '../../services/dashboardService';

export function LabDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchLabDashboard() {
      try {
        setLoading(true);
        const res = await dashboardService.getLabTechnicianDashboard();
        setData(res);
      } catch (err) {
        setError(err.message || 'Failed to load Lab Technician workspace.');
      } finally {
        setLoading(false);
      }
    }
    fetchLabDashboard();
  }, []);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)',
          color: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          padding: '2rem',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.2)', padding: '0.5rem', borderRadius: '10px' }}>
            <FlaskConical size={24} color="#ffffff" />
          </div>
          <Badge variant="purple" style={{ background: '#ffffff', color: '#7c3aed', fontWeight: 700 }}>
            Lab Technician Portal
          </Badge>
        </div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0.25rem 0' }}>
          Welcome, {user?.full_name || 'Lab Specialist'}
        </h1>
        <p style={{ color: 'rgba(255, 255, 255, 0.85)', margin: 0, fontSize: '0.9375rem' }}>
          Clinical diagnostics, diagnostic specimen tracking, and laboratory report management.
        </p>
      </div>

      {loading ? (
        <Card style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
          <Activity size={28} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#7c3aed' }} />
          <div>Loading Laboratory Workspace...</div>
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
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Pending Tests</span>
                <Clock size={18} color="#d97706" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.pending_lab_tests ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#d97706', marginTop: '0.25rem' }}>Awaiting specimen analysis</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Completed Today</span>
                <CheckCircle size={18} color="#059669" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.completed_tests_today ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#059669', marginTop: '0.25rem' }}>Reports published</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Critical Alerts</span>
                <AlertTriangle size={18} color="#e11d48" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.critical_alerts ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', marginTop: '0.25rem' }}>Abnormal values flag</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Samples Processed</span>
                <FlaskConical size={18} color="#7c3aed" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.total_samples_processed ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#7c3aed', marginTop: '0.25rem' }}>Cumulative platform total</div>
            </Card>
          </div>

          {/* Pending Tasks Queue */}
          <Card className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>Active Diagnostic Queue</h3>
              <Badge variant="purple">Foundation Mode</Badge>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {(data?.pending_tasks || []).map((task) => (
                <div
                  key={task.id}
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
                    <div style={{ background: '#ede9fe', padding: '0.5rem', borderRadius: '8px', color: '#7c3aed' }}>
                      <FlaskConical size={16} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{task.test_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Specimen ID: #{task.id + 1040}</div>
                    </div>
                  </div>
                  <Badge variant={task.priority === 'HIGH' ? 'rose' : 'blue'}>{task.priority}</Badge>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

export default LabDashboardPage;
