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
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import pharmacyService from '../../services/pharmacyService';

export function PharmacyPrescriptionsListPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [prescriptions, setPrescriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Search
  const [statusFilter, setStatusFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  const loadPrescriptions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await pharmacyService.getPrescriptions({
        status: statusFilter || undefined,
        risk_level: riskFilter || undefined,
        search: searchQuery || undefined,
        skip: page * limit,
        limit,
      });
      setPrescriptions(res || []);
    } catch (err) {
      setError(err.message || 'Failed to load prescriptions list.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, riskFilter, searchQuery, page]);

  useEffect(() => {
    loadPrescriptions();
  }, [loadPrescriptions]);

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
        return <span style={{ color: 'var(--secondary-400)', fontSize: '0.75rem' }}>No alerts</span>;
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <Link to="/pharmacy/dashboard" style={{ color: 'var(--secondary-500)', textDecoration: 'none', display: 'flex', alignItems: 'center', fontSize: '0.875rem' }}>
              <ArrowLeft size={16} style={{ marginRight: '0.25rem' }} /> Back to Overview
            </Link>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--secondary-900)' }}>
            Prescription Dispensary & Fulfillment Queue
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--secondary-500)', margin: '0.25rem 0 0 0' }}>
            Digital prescription records, AI interaction warnings, and patient medication dispensation.
          </p>
        </div>

        <Button
          variant="outline"
          onClick={loadPrescriptions}
          disabled={loading}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
        </Button>
      </div>

      {/* Filter Bar */}
      <Card className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', flex: 1 }}>
            {/* Search */}
            <div style={{ position: 'relative', minWidth: '240px', flex: 1 }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--secondary-400)' }} />
              <input
                type="text"
                placeholder="Search patient, diagnosis, doctor..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(0);
                }}
                style={{
                  width: '100%',
                  padding: '0.55rem 0.75rem 0.55rem 2.25rem',
                  fontSize: '0.875rem',
                  border: '1px solid var(--secondary-200)',
                  borderRadius: 'var(--radius-md)',
                  outline: 'none',
                }}
              />
            </div>

            {/* Status filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(0);
              }}
              style={{
                padding: '0.55rem 0.85rem',
                fontSize: '0.875rem',
                border: '1px solid var(--secondary-200)',
                borderRadius: 'var(--radius-md)',
                background: '#ffffff',
                outline: 'none',
              }}
            >
              <option value="">All Fulfillment Stages</option>
              <option value="PRESCRIBED">Prescribed (Pending)</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="READY">Ready for Pickup</option>
              <option value="DISPENSED">Dispensed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>

            {/* AI Risk Filter */}
            <select
              value={riskFilter}
              onChange={(e) => {
                setRiskFilter(e.target.value);
                setPage(0);
              }}
              style={{
                padding: '0.55rem 0.85rem',
                fontSize: '0.875rem',
                border: '1px solid var(--secondary-200)',
                borderRadius: 'var(--radius-md)',
                background: '#ffffff',
                outline: 'none',
              }}
            >
              <option value="">All AI Risk Levels</option>
              <option value="CRITICAL">Critical Risk Only</option>
              <option value="HIGH">High Risk Only</option>
              <option value="MODERATE">Moderate Risk</option>
              <option value="LOW">Low Risk</option>
            </select>
          </div>

          {(searchQuery || statusFilter || riskFilter) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('');
                setRiskFilter('');
                setPage(0);
              }}
              style={{ color: 'var(--secondary-500)', fontSize: '0.8125rem' }}
            >
              Reset Filters
            </Button>
          )}
        </div>
      </Card>

      {/* Prescription Queue Table */}
      <Card className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
        {error && (
          <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '1rem', margin: '1rem', borderRadius: 'var(--radius-md)' }}>
            <AlertTriangle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} /> {error}
          </div>
        )}

        {loading ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <Activity size={32} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#0d9488' }} />
            <div>Loading prescriptions...</div>
          </div>
        ) : prescriptions.length === 0 ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <Pill size={40} style={{ margin: '0 auto 1rem auto', opacity: 0.3 }} />
            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--secondary-700)' }}>No prescriptions match the criteria</div>
            <div style={{ fontSize: '0.875rem', color: 'var(--secondary-400)', marginTop: '0.25rem' }}>
              Adjust search keywords or status filter to browse dispensary records.
            </div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ background: 'var(--secondary-50)', borderBottom: '1px solid var(--secondary-200)', color: 'var(--secondary-600)', textAlign: 'left' }}>
                  <th style={{ padding: '0.875rem 1.25rem' }}>Prescription ID</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Patient</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Prescribing Doctor</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Medications</th>
                  <th style={{ padding: '0.875rem 1rem' }}>AI Safety Insights</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Status</th>
                  <th style={{ padding: '0.875rem 1.25rem', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {prescriptions.map((rx) => (
                  <tr
                    key={rx.id}
                    style={{
                      borderBottom: '1px solid var(--secondary-100)',
                      backgroundColor: rx.ai_risk_level === 'HIGH' || rx.ai_risk_level === 'CRITICAL' ? 'rgba(254, 226, 226, 0.25)' : 'transparent',
                      transition: 'background-color 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '1rem 1.25rem', fontWeight: 700, color: 'var(--secondary-900)' }}>
                      #{rx.id}
                    </td>
                    <td style={{ padding: '1rem 1rem' }}>
                      <div style={{ fontWeight: 600, color: 'var(--secondary-900)' }}>{rx.patient_name}</div>
                      {rx.patient_age && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                          {rx.patient_age} yrs • {rx.patient_gender || ''}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '1rem 1rem' }}>
                      <div style={{ color: 'var(--secondary-800)', fontWeight: 500 }}>{rx.doctor_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>{rx.doctor_specialization || 'Physician'}</div>
                    </td>
                    <td style={{ padding: '1rem 1rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {(rx.medication_names || []).slice(0, 2).map((med, idx) => (
                          <span key={idx} style={{ fontSize: '0.8125rem', color: 'var(--secondary-800)' }}>• {med}</span>
                        ))}
                        {(rx.medication_names || []).length > 2 && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                            +{(rx.medication_names || []).length - 2} more
                          </span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '1rem 1rem' }}>
                      {getRiskBadge(rx.ai_risk_level)}
                    </td>
                    <td style={{ padding: '1rem 1rem' }}>
                      {getStatusBadge(rx.status)}
                    </td>
                    <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => navigate(`/pharmacy/prescriptions/${rx.id}`)}
                        style={{
                          background: '#0d9488',
                          borderColor: '#0d9488',
                          fontSize: '0.75rem',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                        }}
                      >
                        <Eye size={13} /> Dispensary
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
        <div style={{ padding: '1rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--secondary-200)' }}>
          <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
            Showing page {page + 1} ({prescriptions.length} prescriptions)
          </span>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Button
              size="sm"
              variant="outline"
              disabled={page === 0 || loading}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              <ChevronLeft size={14} /> Previous
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={prescriptions.length < limit || loading}
              onClick={() => setPage((p) => p + 1)}
            >
              Next <ChevronRight size={14} />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default PharmacyPrescriptionsListPage;
