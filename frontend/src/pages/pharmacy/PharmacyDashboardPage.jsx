import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Pill,
  Activity,
  CheckCircle,
  AlertTriangle,
  Clock,
  PackageCheck,
  Search,
  RefreshCw,
  Eye,
  ShieldAlert,
  ArrowUpRight,
  Sparkles,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import pharmacyService from '../../services/pharmacyService';

export function PharmacyDashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await pharmacyService.getDashboard();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load Pharmacy Staff workspace.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PRESCRIBED':
        return <Badge variant="amber">Prescribed (Pending)</Badge>;
      case 'UNDER_REVIEW':
        return <Badge variant="blue">Under Review</Badge>;
      case 'READY':
        return <Badge variant="teal">Ready for Pickup</Badge>;
      case 'DISPENSED':
        return <Badge variant="green">Dispensed</Badge>;
      case 'CANCELLED':
        return <Badge variant="rose">Cancelled</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'CRITICAL':
        return <Badge variant="rose">CRITICAL RISK</Badge>;
      case 'HIGH':
        return <Badge variant="rose">HIGH RISK</Badge>;
      case 'MODERATE':
        return <Badge variant="amber">MODERATE</Badge>;
      case 'LOW':
        return <Badge variant="teal">LOW RISK</Badge>;
      default:
        return null;
    }
  };

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
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.2)', padding: '0.5rem', borderRadius: '10px' }}>
              <Pill size={24} color="#ffffff" />
            </div>
            <Badge variant="teal" style={{ background: '#ffffff', color: '#0d9488', fontWeight: 700 }}>
              Pharmacy Staff Dispensary Console
            </Badge>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0.25rem 0' }}>
            Welcome, {user?.full_name || 'Pharmacist'}
          </h1>
          <p style={{ color: 'rgba(255, 255, 255, 0.85)', margin: 0, fontSize: '0.9375rem' }}>
            Prescription fulfillment, AI pharmacotherapy safety checks, and clinical medication dispensing.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Button
            variant="outline"
            onClick={() => navigate('/pharmacy/prescriptions')}
            style={{ background: 'rgba(255, 255, 255, 0.15)', color: '#ffffff', borderColor: '#ffffff' }}
          >
            All Prescriptions <ArrowUpRight size={15} style={{ marginLeft: '0.25rem' }} />
          </Button>

          <Button
            variant="outline"
            onClick={loadDashboard}
            disabled={loading}
            style={{ background: '#ffffff', color: '#0d9488', borderColor: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <Card style={{ padding: '4rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
          <Activity size={32} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#0d9488' }} />
          <div>Loading Pharmacy Workspace Metrics...</div>
        </Card>
      ) : error ? (
        <Card style={{ padding: '2rem', background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c' }}>
          <AlertTriangle size={24} style={{ marginBottom: '0.5rem' }} />
          <div style={{ fontWeight: 700 }}>{error}</div>
        </Card>
      ) : (
        <>
          {/* Key Operational Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Pending Review</span>
                <Clock size={18} color="#d97706" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.pending_dispensations ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#d97706', marginTop: '0.25rem' }}>Newly prescribed</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Under Review</span>
                <Activity size={18} color="#0284c7" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.under_review_count ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#0284c7', marginTop: '0.25rem' }}>Active pharmacist verification</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Ready for Pickup</span>
                <CheckCircle size={18} color="#0d9488" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.ready_for_pickup_count ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#0d9488', marginTop: '0.25rem' }}>Packaged for patient</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Dispensed Today</span>
                <PackageCheck size={18} color="#059669" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.dispensed_today ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#059669', marginTop: '0.25rem' }}>Fulfillment verified</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Safety Alerts</span>
                <ShieldAlert size={18} color="#e11d48" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#e11d48' }}>
                {data?.stats?.high_risk_alerts_count ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#e11d48', marginTop: '0.25rem' }}>High/Critical interactions</div>
            </Card>

            <Card className="glass-panel" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Total Dispensed</span>
                <PackageCheck size={18} color="var(--primary-600)" />
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                {data?.stats?.total_medications_dispensed ?? 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', marginTop: '0.25rem' }}>Cumulative platform items</div>
            </Card>
          </div>

          {/* Pending Dispensations Queue */}
          <Card className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Pill size={20} color="#0d9488" /> Active Prescription Fulfillment Queue
                </h3>
                <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                  Review medication dosages, AI safety insights, and manage patient dispensing.
                </span>
              </div>

              <Link
                to="/pharmacy/prescriptions"
                style={{
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  color: '#0d9488',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                }}
              >
                View Complete Work Queue →
              </Link>
            </div>

            {(data?.pending_dispensations || []).length === 0 ? (
              <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
                <Pill size={36} style={{ margin: '0 auto 0.75rem auto', opacity: 0.3 }} />
                <div style={{ fontWeight: 600 }}>No prescriptions currently awaiting fulfillment.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {(data?.pending_dispensations || []).map((disp) => (
                  <div
                    key={disp.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '1rem 1.25rem',
                      background: 'var(--bg-main)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--secondary-200)',
                      flexWrap: 'wrap',
                      gap: '0.75rem',
                      transition: 'border-color 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1, minWidth: '240px' }}>
                      <div style={{ background: '#ccfbf1', padding: '0.625rem', borderRadius: '10px', color: '#0f766e' }}>
                        <Pill size={20} />
                      </div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--secondary-900)' }}>
                            Prescription #{disp.id}
                          </span>
                          {getStatusBadge(disp.status)}
                          {getRiskBadge(disp.ai_risk_level)}
                        </div>
                        <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-600)', marginTop: '0.25rem' }}>
                          Patient: <strong>{disp.patient_name}</strong> • Prescribed by: {disp.doctor_name}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', marginTop: '0.125rem' }}>
                          Medication(s): {disp.medication_names?.join(', ') || disp.medication}
                        </div>
                      </div>
                    </div>

                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => navigate(`/pharmacy/prescriptions/${disp.id}`)}
                      style={{
                        background: '#0d9488',
                        borderColor: '#0d9488',
                        fontSize: '0.8125rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.375rem',
                      }}
                    >
                      <Eye size={14} /> Open Dispensary
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}

export default PharmacyDashboardPage;
