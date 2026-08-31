import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FlaskConical,
  Activity,
  CheckCircle,
  AlertTriangle,
  Clock,
  Search,
  Filter,
  RefreshCw,
  Eye,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  FileText,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import labService from '../../services/labService';

export function LabTestsListPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters and pagination
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  const loadOrders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await labService.getWorkQueue({
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        search: searchQuery || undefined,
        skip: page * limit,
        limit,
      });
      setOrders(res || []);
    } catch (err) {
      setError(err.message || 'Failed to load diagnostic orders.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, searchQuery, page]);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'STAT':
        return <Badge variant="rose" style={{ animation: 'pulse 2s infinite' }}>STAT</Badge>;
      case 'URGENT':
        return <Badge variant="amber">URGENT</Badge>;
      default:
        return <Badge variant="blue">ROUTINE</Badge>;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'SAMPLE_PENDING':
      case 'ORDERED':
        return <Badge variant="amber">Sample Pending</Badge>;
      case 'SAMPLE_COLLECTED':
        return <Badge variant="teal">Sample Collected</Badge>;
      case 'IN_PROGRESS':
        return <Badge variant="purple">In Testing</Badge>;
      case 'RESULTS_ENTERED':
        return <Badge variant="blue">Results Entered</Badge>;
      case 'VERIFIED':
        return <Badge variant="teal">Verified</Badge>;
      case 'RELEASED':
        return <Badge variant="green">Released</Badge>;
      case 'CANCELLED':
        return <Badge variant="rose">Cancelled</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <Link to="/lab/dashboard" style={{ color: 'var(--secondary-500)', textDecoration: 'none', display: 'flex', alignItems: 'center', fontSize: '0.875rem' }}>
              <ArrowLeft size={16} style={{ marginRight: '0.25rem' }} /> Back to Overview
            </Link>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--secondary-900)' }}>
            Diagnostic Test Requisitions & Work Queue
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--secondary-500)', margin: '0.25rem 0 0 0' }}>
            Manage clinical accessioning, specimen analysis, result verification, and diagnostic releases.
          </p>
        </div>

        <Button
          variant="outline"
          onClick={loadOrders}
          disabled={loading}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <Card className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', flex: 1 }}>
            {/* Search */}
            <div style={{ position: 'relative', minWidth: '240px', flex: 1 }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--secondary-400)' }} />
              <input
                type="text"
                placeholder="Search patient, order ID, or doctor..."
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

            {/* Priority filter */}
            <select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
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
              <option value="">All Priorities</option>
              <option value="STAT">STAT Immediate</option>
              <option value="URGENT">Urgent</option>
              <option value="ROUTINE">Routine</option>
            </select>

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
              <option value="">All Workflow Stages</option>
              <option value="SAMPLE_PENDING">Sample Pending</option>
              <option value="SAMPLE_COLLECTED">Sample Collected</option>
              <option value="IN_PROGRESS">In Testing</option>
              <option value="RESULTS_ENTERED">Results Entered</option>
              <option value="VERIFIED">Verified</option>
              <option value="RELEASED">Released</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          {(searchQuery || priorityFilter || statusFilter) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearchQuery('');
                setPriorityFilter('');
                setStatusFilter('');
                setPage(0);
              }}
              style={{ color: 'var(--secondary-500)', fontSize: '0.8125rem' }}
            >
              Reset Filters
            </Button>
          )}
        </div>
      </Card>

      {/* Orders Table */}
      <Card className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
        {error && (
          <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '1rem', margin: '1rem', borderRadius: 'var(--radius-md)' }}>
            <AlertTriangle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} /> {error}
          </div>
        )}

        {loading ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <Activity size={32} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#7c3aed' }} />
            <div>Loading requisitions...</div>
          </div>
        ) : orders.length === 0 ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <FlaskConical size={40} style={{ margin: '0 auto 1rem auto', opacity: 0.3 }} />
            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--secondary-700)' }}>No requisitions found</div>
            <div style={{ fontSize: '0.875rem', color: 'var(--secondary-400)', marginTop: '0.25rem' }}>
              Try adjusting your search criteria or filter options.
            </div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ background: 'var(--secondary-50)', borderBottom: '1px solid var(--secondary-200)', color: 'var(--secondary-600)', textAlign: 'left' }}>
                  <th style={{ padding: '0.875rem 1.25rem' }}>Order ID</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Priority</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Patient Name</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Ordering Physician</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Diagnostic Tests</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Ordered Date</th>
                  <th style={{ padding: '0.875rem 1rem' }}>Workflow Stage</th>
                  <th style={{ padding: '0.875rem 1.25rem', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr
                    key={order.id}
                    style={{
                      borderBottom: '1px solid var(--secondary-100)',
                      backgroundColor: order.is_critical_flagged ? 'rgba(254, 226, 226, 0.25)' : 'transparent',
                      transition: 'background-color 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '1rem 1.25rem', fontWeight: 700, color: 'var(--secondary-900)' }}>
                      #{order.id}
                    </td>
                    <td style={{ padding: '1rem 1rem' }}>{getPriorityBadge(order.priority)}</td>
                    <td style={{ padding: '1rem 1rem', fontWeight: 600, color: 'var(--secondary-900)' }}>
                      {order.patient_name}
                    </td>
                    <td style={{ padding: '1rem 1rem', color: 'var(--secondary-700)' }}>
                      {order.doctor_name}
                    </td>
                    <td style={{ padding: '1rem 1rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {order.test_names.slice(0, 2).map((t, idx) => (
                          <span key={idx} style={{ fontSize: '0.8125rem', color: 'var(--secondary-800)' }}>• {t}</span>
                        ))}
                        {order.test_names.length > 2 && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>+{order.test_names.length - 2} more</span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '1rem 1rem', color: 'var(--secondary-500)', fontSize: '0.8125rem' }}>
                      {order.ordered_at ? new Date(order.ordered_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td style={{ padding: '1rem 1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                        {getStatusBadge(order.status)}
                        {order.is_critical_flagged && (
                          <Badge variant="rose" style={{ fontSize: '0.625rem' }}>CRITICAL</Badge>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }}>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => navigate(`/lab/tests/${order.id}`)}
                        style={{
                          background: '#7c3aed',
                          borderColor: '#7c3aed',
                          fontSize: '0.75rem',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                        }}
                      >
                        <Eye size={13} /> Workstation
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        <div style={{ padding: '1rem 1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--secondary-200)' }}>
          <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
            Showing page {page + 1} ({orders.length} requisitions)
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
              disabled={orders.length < limit || loading}
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

export default LabTestsListPage;
