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
  FileText,
  ChevronRight,
  ShieldCheck,
  Eye,
  AlertCircle,
  X,
  Sparkles,
  ArrowUpRight,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import labService from '../../services/labService';

export function LabDashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter and Search states
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Active Modals state
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [activeModal, setActiveModal] = useState(null); // 'COLLECT', 'RESULTS', 'VERIFY'
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);

  // Form states for modals
  const [sampleCondition, setSampleCondition] = useState('ACCEPTABLE');
  const [specimenType, setSpecimenType] = useState('Whole Blood (EDTA)');
  const [collectionNotes, setCollectionNotes] = useState('');
  const [resultInputs, setResultInputs] = useState({});
  const [verificationNotes, setVerificationNotes] = useState('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsRes, queueRes] = await Promise.all([
        labService.getQueueStats(),
        labService.getWorkQueue({
          status: statusFilter || undefined,
          priority: priorityFilter || undefined,
          search: searchQuery || undefined,
          limit: 10,
        }),
      ]);
      setStats(statsRes);
      setQueue(queueRes || []);
    } catch (err) {
      setError(err.message || 'Failed to load laboratory queue data.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Open modal helpers
  const handleOpenCollect = async (order) => {
    try {
      setActionLoading(true);
      setActionError(null);
      const fullOrder = await labService.getOrder(order.id);
      setSelectedOrder(fullOrder);
      setSpecimenType(fullOrder.items[0]?.test?.specimen_type || 'Whole Blood (EDTA)');
      setSampleCondition('ACCEPTABLE');
      setCollectionNotes('');
      setActiveModal('COLLECT');
    } catch (err) {
      setError(err.message || 'Failed to fetch order details.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenResults = async (order) => {
    try {
      setActionLoading(true);
      setActionError(null);
      const fullOrder = await labService.getOrder(order.id);
      setSelectedOrder(fullOrder);
      const initial = {};
      fullOrder.items.forEach((item) => {
        initial[item.id] = {
          numeric_value: item.result?.numeric_value ?? '',
          text_value: item.result?.text_value ?? '',
          unit: item.result?.unit || item.test?.unit || '',
          reference_range: item.result?.reference_range || item.test?.reference_range || '',
        };
      });
      setResultInputs(initial);
      setActiveModal('RESULTS');
    } catch (err) {
      setError(err.message || 'Failed to fetch order details.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenVerify = async (order) => {
    try {
      setActionLoading(true);
      setActionError(null);
      const fullOrder = await labService.getOrder(order.id);
      setSelectedOrder(fullOrder);
      setVerificationNotes('');
      setActiveModal('VERIFY');
    } catch (err) {
      setError(err.message || 'Failed to fetch order details.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartProcessing = async (orderId) => {
    try {
      setActionLoading(true);
      await labService.startProcessing(orderId);
      await loadData();
    } catch (err) {
      alert(err.message || 'Failed to start testing.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitCollection = async (e) => {
    e.preventDefault();
    if (!selectedOrder) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await labService.collectSample(selectedOrder.id, {
        specimen_type: specimenType,
        sample_condition: sampleCondition,
        collection_notes: collectionNotes,
      });
      setActiveModal(null);
      await loadData();
    } catch (err) {
      setActionError(err.message || 'Failed to record specimen collection.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitResults = async (e) => {
    e.preventDefault();
    if (!selectedOrder) return;
    try {
      setActionLoading(true);
      setActionError(null);

      const batchResults = selectedOrder.items.map((item) => {
        const input = resultInputs[item.id] || {};
        return {
          lab_order_item_id: item.id,
          numeric_value: input.numeric_value !== '' ? parseFloat(input.numeric_value) : null,
          text_value: input.text_value || null,
          unit: input.unit || null,
          reference_range: input.reference_range || null,
        };
      });

      await labService.enterResults(selectedOrder.id, { results: batchResults });
      setActiveModal(null);
      await loadData();
    } catch (err) {
      setActionError(err.message || 'Failed to save diagnostic results.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitVerify = async (e) => {
    e.preventDefault();
    if (!selectedOrder) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await labService.verifyResults(selectedOrder.id, verificationNotes);
      setActiveModal(null);
      await loadData();
    } catch (err) {
      setActionError(err.message || 'Failed to verify results.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRelease = async (orderId) => {
    if (!window.confirm('Are you sure you want to release this verified diagnostic report to the patient and ordering doctor?')) return;
    try {
      setActionLoading(true);
      await labService.releaseResults(orderId);
      await loadData();
    } catch (err) {
      alert(err.message || 'Failed to release report.');
    } finally {
      setActionLoading(false);
    }
  };

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
      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)',
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
              <FlaskConical size={24} color="#ffffff" />
            </div>
            <Badge variant="purple" style={{ background: '#ffffff', color: '#7c3aed', fontWeight: 700 }}>
              Laboratory Technician Operational Console
            </Badge>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0.25rem 0' }}>
            Welcome, {user?.full_name || 'Lab Specialist'}
          </h1>
          <p style={{ color: 'rgba(255, 255, 255, 0.85)', margin: 0, fontSize: '0.9375rem' }}>
            Diagnostic requisition queue, specimen collection, analytical testing, and verification.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Button
            variant="outline"
            onClick={() => navigate('/lab/tests')}
            style={{ background: 'rgba(255, 255, 255, 0.15)', color: '#ffffff', borderColor: '#ffffff' }}
          >
            All Requisitions <ArrowUpRight size={15} style={{ marginLeft: '0.25rem' }} />
          </Button>

          <Button
            variant="outline"
            onClick={loadData}
            disabled={loading}
            style={{ background: '#ffffff', color: '#7c3aed', borderColor: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
          </Button>
        </div>
      </div>

      {/* Operational Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Pending Samples</span>
            <Clock size={18} color="#d97706" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
            {stats?.pending_samples ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#d97706', marginTop: '0.25rem' }}>Awaiting collection</div>
        </Card>

        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Collected Today</span>
            <CheckCircle size={18} color="#0d9488" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
            {stats?.samples_collected_today ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#0d9488', marginTop: '0.25rem' }}>Specimens received</div>
        </Card>

        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>In Testing</span>
            <Activity size={18} color="#7c3aed" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
            {stats?.tests_in_progress ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#7c3aed', marginTop: '0.25rem' }}>Active processing</div>
        </Card>

        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Awaiting Verification</span>
            <ShieldCheck size={18} color="#0284c7" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
            {stats?.results_awaiting_verification ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#0284c7', marginTop: '0.25rem' }}>Results entered</div>
        </Card>

        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Critical Alerts</span>
            <AlertTriangle size={18} color="#e11d48" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#e11d48' }}>
            {stats?.critical_alerts_count ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#e11d48', marginTop: '0.25rem' }}>Panic values flagged</div>
        </Card>

        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)' }}>Completed Today</span>
            <CheckCircle size={18} color="#059669" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
            {stats?.completed_tests_today ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#059669', marginTop: '0.25rem' }}>Reports released</div>
        </Card>
      </div>

      {/* Main Work Queue Table */}
      <Card className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FlaskConical size={20} color="#7c3aed" /> Active Diagnostic Requisitions
            </h3>
            <Link to="/lab/tests" style={{ fontSize: '0.8125rem', color: '#7c3aed', fontWeight: 600, textDecoration: 'none' }}>
              View All Queue →
            </Link>
          </div>

          {/* Filter Bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', width: '200px' }}>
              <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--secondary-400)' }} />
              <input
                type="text"
                placeholder="Search patient/order..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.45rem 0.75rem 0.45rem 2rem',
                  fontSize: '0.8125rem',
                  border: '1px solid var(--secondary-200)',
                  borderRadius: 'var(--radius-md)',
                  outline: 'none',
                }}
              />
            </div>

            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              style={{
                padding: '0.45rem 0.75rem',
                fontSize: '0.8125rem',
                border: '1px solid var(--secondary-200)',
                borderRadius: 'var(--radius-md)',
                background: '#ffffff',
                outline: 'none',
              }}
            >
              <option value="">All Priorities</option>
              <option value="STAT">STAT</option>
              <option value="URGENT">URGENT</option>
              <option value="ROUTINE">ROUTINE</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                padding: '0.45rem 0.75rem',
                fontSize: '0.8125rem',
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
            </select>
          </div>
        </div>

        {error && (
          <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
            <AlertTriangle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} /> {error}
          </div>
        )}

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <Activity size={28} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#7c3aed' }} />
            <div>Loading Work Queue...</div>
          </div>
        ) : queue.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <FlaskConical size={36} style={{ margin: '0 auto 0.75rem auto', opacity: 0.4 }} />
            <div style={{ fontWeight: 600 }}>No laboratory orders match your current filters.</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--secondary-200)', color: 'var(--secondary-600)', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Order ID</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Priority</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Patient</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Ordering Doctor</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Tests Requested</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {queue.map((order) => (
                  <tr
                    key={order.id}
                    style={{
                      borderBottom: '1px solid var(--secondary-100)',
                      backgroundColor: order.is_critical_flagged ? 'rgba(254, 226, 226, 0.3)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: 'var(--secondary-900)' }}>
                      <Link to={`/lab/tests/${order.id}`} style={{ color: '#7c3aed', textDecoration: 'none' }}>
                        #{order.id}
                      </Link>
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>{getPriorityBadge(order.priority)}</td>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 600 }}>{order.patient_name}</td>
                    <td style={{ padding: '0.875rem 1rem', color: 'var(--secondary-700)' }}>{order.doctor_name}</td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {order.test_names.slice(0, 2).map((t, idx) => (
                          <span key={idx} style={{ fontSize: '0.8125rem', color: 'var(--secondary-800)' }}>• {t}</span>
                        ))}
                        {order.test_names.length > 2 && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>+{order.test_names.length - 2} more</span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                        {getStatusBadge(order.status)}
                        {order.is_critical_flagged && (
                          <Badge variant="rose" style={{ fontSize: '0.625rem' }}>CRITICAL</Badge>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.375rem' }}>
                        {(order.status === 'ORDERED' || order.status === 'SAMPLE_PENDING') && (
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleOpenCollect(order)}
                            style={{ background: '#7c3aed', borderColor: '#7c3aed', padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                          >
                            Collect Specimen
                          </Button>
                        )}

                        {order.status === 'SAMPLE_COLLECTED' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleStartProcessing(order.id)}
                            style={{ color: '#7c3aed', borderColor: '#7c3aed', padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                          >
                            Start Testing
                          </Button>
                        )}

                        {(order.status === 'IN_PROGRESS' || order.status === 'SAMPLE_COLLECTED') && (
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleOpenResults(order)}
                            style={{ background: '#0284c7', borderColor: '#0284c7', padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                          >
                            Enter Results
                          </Button>
                        )}

                        {order.status === 'RESULTS_ENTERED' && (
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleOpenVerify(order)}
                            style={{ background: '#0d9488', borderColor: '#0d9488', padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                          >
                            Verify Results
                          </Button>
                        )}

                        {order.status === 'VERIFIED' && (
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleRelease(order.id)}
                            style={{ background: '#059669', borderColor: '#059669', padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                          >
                            Release Report
                          </Button>
                        )}

                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => navigate(`/lab/tests/${order.id}`)}
                          style={{ padding: '0.35rem 0.5rem', color: 'var(--secondary-600)' }}
                          title="Open Workstation Detail"
                        >
                          <Eye size={15} />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal 1: Collect Specimen */}
      {activeModal === 'COLLECT' && selectedOrder && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '540px', width: '100%', padding: '1.75rem', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FlaskConical size={20} color="#7c3aed" /> Record Specimen Collection
              </h3>
              <button type="button" onClick={() => setActiveModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)' }}>
                <X size={20} />
              </button>
            </div>

            {actionError && (
              <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.8125rem' }}>
                {actionError}
              </div>
            )}

            <form onSubmit={handleSubmitCollection} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Order Requisition
                </label>
                <div style={{ fontSize: '0.875rem', color: 'var(--secondary-900)', fontWeight: 600 }}>
                  Order #{selectedOrder.id} • Patient: {selectedOrder.patient_name}
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Specimen Type
                </label>
                <input
                  type="text"
                  required
                  value={specimenType}
                  onChange={(e) => setSpecimenType(e.target.value)}
                  placeholder="e.g. Whole Blood (EDTA), Serum (SST), Urine"
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Specimen Condition
                </label>
                <select
                  value={sampleCondition}
                  onChange={(e) => setSampleCondition(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                >
                  <option value="ACCEPTABLE">ACCEPTABLE (Sample integrity verified)</option>
                  <option value="HEMOLYZED">HEMOLYZED (Recollection required)</option>
                  <option value="CLOTTED">CLOTTED (Recollection required)</option>
                  <option value="INSUFFICIENT">INSUFFICIENT (Quantity not sufficient)</option>
                  <option value="CONTAMINATED">CONTAMINATED (Sterility compromised)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Collection Notes
                </label>
                <textarea
                  rows={3}
                  value={collectionNotes}
                  onChange={(e) => setCollectionNotes(e.target.value)}
                  placeholder="Draw site, collection notes..."
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <Button variant="ghost" type="button" onClick={() => setActiveModal(null)}>Cancel</Button>
                <Button variant="primary" type="submit" disabled={actionLoading} style={{ background: '#7c3aed' }}>
                  {actionLoading ? 'Saving...' : 'Confirm Specimen'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal 2: Result Entry */}
      {activeModal === 'RESULTS' && selectedOrder && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '780px', width: '100%', maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: 'var(--shadow-lg)', overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.75rem', borderBottom: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileText size={20} color="#0284c7" /> Analytical Result Entry
                </h3>
                <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                  Order #{selectedOrder.id} • Patient: {selectedOrder.patient_name}
                </span>
              </div>
              <button type="button" onClick={() => setActiveModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '1.5rem 1.75rem', overflowY: 'auto', flex: 1 }}>
              {actionError && (
                <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.8125rem' }}>
                  {actionError}
                </div>
              )}

              <form id="result-entry-form" onSubmit={handleSubmitResults} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {selectedOrder.items.map((item) => {
                  const input = resultInputs[item.id] || {};
                  return (
                    <Card key={item.id} style={{ padding: '1.25rem', border: '1px solid var(--secondary-200)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--secondary-900)' }}>
                            {item.test.test_name}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                            Code: {item.test.test_code} • Category: {item.test.category}
                          </div>
                        </div>
                        <Badge variant="teal">{item.test.reference_range ? `Ref: ${item.test.reference_range} ${item.test.unit || ''}` : 'Qualitative'}</Badge>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 120px', gap: '0.75rem' }}>
                        <div>
                          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--secondary-600)', display: 'block', marginBottom: '0.25rem' }}>
                            Numeric Value
                          </label>
                          <input
                            type="number"
                            step="any"
                            value={input.numeric_value}
                            onChange={(e) => {
                              const val = e.target.value;
                              setResultInputs((prev) => ({
                                ...prev,
                                [item.id]: { ...prev[item.id], numeric_value: val },
                              }));
                            }}
                            placeholder="e.g. 14.2"
                            style={{ width: '100%', padding: '0.45rem 0.65rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                          />
                        </div>

                        <div>
                          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--secondary-600)', display: 'block', marginBottom: '0.25rem' }}>
                            Qualitative Text (Optional)
                          </label>
                          <input
                            type="text"
                            value={input.text_value}
                            onChange={(e) => {
                              const val = e.target.value;
                              setResultInputs((prev) => ({
                                ...prev,
                                [item.id]: { ...prev[item.id], text_value: val },
                              }));
                            }}
                            placeholder="e.g. Negative"
                            style={{ width: '100%', padding: '0.45rem 0.65rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                          />
                        </div>

                        <div>
                          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--secondary-600)', display: 'block', marginBottom: '0.25rem' }}>
                            Unit
                          </label>
                          <input
                            type="text"
                            value={input.unit}
                            onChange={(e) => {
                              const val = e.target.value;
                              setResultInputs((prev) => ({
                                ...prev,
                                [item.id]: { ...prev[item.id], unit: val },
                              }));
                            }}
                            placeholder="Unit"
                            style={{ width: '100%', padding: '0.45rem 0.65rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                          />
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </form>
            </div>

            <div style={{ padding: '1rem 1.75rem', borderTop: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="ghost" type="button" onClick={() => setActiveModal(null)}>Cancel</Button>
              <Button form="result-entry-form" variant="primary" type="submit" disabled={actionLoading} style={{ background: '#0284c7' }}>
                {actionLoading ? 'Saving...' : 'Save Analytical Results'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 3: Verification */}
      {activeModal === 'VERIFY' && selectedOrder && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '540px', width: '100%', padding: '1.75rem', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ShieldCheck size={20} color="#0d9488" /> Clinical Result Verification
              </h3>
              <button type="button" onClick={() => setActiveModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)' }}>
                <X size={20} />
              </button>
            </div>

            {actionError && (
              <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.8125rem' }}>
                {actionError}
              </div>
            )}

            <form onSubmit={handleSubmitVerify} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Verification Confirmation
                </label>
                <div style={{ fontSize: '0.875rem', color: 'var(--secondary-800)', lineHeight: 1.5 }}>
                  Confirming verification locks results, applies diagnostic validation audit stamps, and prepares report for release to patient and physician.
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Verification Notes / Quality Control Observations (Optional)
                </label>
                <textarea
                  rows={3}
                  value={verificationNotes}
                  onChange={(e) => setVerificationNotes(e.target.value)}
                  placeholder="Controls within acceptable standard deviations..."
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <Button variant="ghost" type="button" onClick={() => setActiveModal(null)}>Cancel</Button>
                <Button variant="primary" type="submit" disabled={actionLoading} style={{ background: '#0d9488' }}>
                  {actionLoading ? 'Verifying...' : 'Confirm Verification'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default LabDashboardPage;
