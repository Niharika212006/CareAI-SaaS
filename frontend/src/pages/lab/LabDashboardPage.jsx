import React, { useState, useEffect, useCallback } from 'react';
import {
  FlaskConical,
  Activity,
  CheckCircle,
  AlertTriangle,
  Clock,
  Search,
  Filter,
  RefreshCw,
  Plus,
  FileText,
  ChevronRight,
  ShieldCheck,
  Send,
  Eye,
  AlertCircle,
  X,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import labService from '../../services/labService';

export function LabDashboardPage() {
  const { user } = useAuth();

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
  const [activeModal, setActiveModal] = useState(null); // 'COLLECT', 'RESULTS', 'VERIFY', 'DETAIL'
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
      // Initialize inputs from existing results if any
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

  const handleOpenDetail = async (order) => {
    try {
      setActionLoading(true);
      const fullOrder = await labService.getOrder(order.id);
      setSelectedOrder(fullOrder);
      setActiveModal('DETAIL');
    } catch (err) {
      setError(err.message || 'Failed to fetch order details.');
    } finally {
      setActionLoading(false);
    }
  };

  // Workflow Handlers
  const handleStartProcessing = async (orderId) => {
    try {
      setActionLoading(true);
      await labService.startProcessing(orderId);
      await loadData();
    } catch (err) {
      alert(err.message || 'Failed to start processing.');
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
        return <Badge variant="rose" style={{ animation: 'pulse 2s infinite' }}>STAT IMMEDIATE</Badge>;
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

        <Button
          variant="outline"
          onClick={loadData}
          disabled={loading}
          style={{ background: '#ffffff', color: '#7c3aed', borderColor: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh Queue
        </Button>
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
          <div style={{ fontSize: '0.75rem', color: '#e11d48', marginTop: '0.25rem' }}>Panic values detected</div>
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
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FlaskConical size={20} color="#7c3aed" /> Diagnostic Requisition Work Queue
          </h3>

          {/* Filter Bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            {/* Search Input */}
            <div style={{ position: 'relative', width: '220px' }}>
              <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--secondary-400)' }} />
              <input
                type="text"
                placeholder="Search patient / order..."
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

            {/* Priority Filter */}
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

            {/* Status Filter */}
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
                      #{order.id}
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
                        {/* Step 1: Collect Sample */}
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

                        {/* Step 2: Start Testing */}
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

                        {/* Step 3: Enter Results */}
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

                        {/* Step 4: Verify */}
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

                        {/* Step 5: Release */}
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

                        {/* View Full Timeline/Details */}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleOpenDetail(order)}
                          style={{ padding: '0.35rem 0.5rem', color: 'var(--secondary-600)' }}
                          title="View Order Details"
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

      {/* ------------------------------------------------------------- */}
      {/* MODAL 1: SPECIMEN COLLECTION */}
      {/* ------------------------------------------------------------- */}
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
                  <option value="INSUFFICIENT">INSUFFICIENT (QNS - Quantity Not Sufficient)</option>
                  <option value="CONTAMINATED">CONTAMINATED (Sterility compromised)</option>
                </select>
              </div>

              {sampleCondition !== 'ACCEPTABLE' && (
                <div style={{ background: '#fffbeb', border: '1px solid #fde68a', color: '#b45309', padding: '0.75rem', borderRadius: 'var(--radius-md)', fontSize: '0.8125rem' }}>
                  <AlertTriangle size={15} style={{ display: 'inline', marginRight: '0.375rem' }} />
                  Compromised specimen will trigger a rejection event and notify the ordering physician that recollection is required.
                </div>
              )}

              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Collection Notes / Draw Observations
                </label>
                <textarea
                  rows={3}
                  value={collectionNotes}
                  onChange={(e) => setCollectionNotes(e.target.value)}
                  placeholder="Record draw site, volume, hemolysis notes, or collection difficulty..."
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

      {/* ------------------------------------------------------------- */}
      {/* MODAL 2: RESULT ENTRY */}
      {/* ------------------------------------------------------------- */}
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
                            placeholder="e.g. Negative, Reactive"
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
                {actionLoading ? 'Saving...' : 'Save & Evaluate Flags'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODAL 3: VERIFICATION */}
      {/* ------------------------------------------------------------- */}
      {activeModal === 'VERIFY' && selectedOrder && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '640px', width: '100%', padding: '1.75rem', boxShadow: 'var(--shadow-lg)' }}>
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

            {/* Results Review Table */}
            <div style={{ marginBottom: '1rem', maxHeight: '200px', overflowY: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--secondary-200)', color: 'var(--secondary-600)' }}>
                    <th style={{ textAlign: 'left', padding: '0.4rem 0' }}>Test</th>
                    <th style={{ textAlign: 'left', padding: '0.4rem 0' }}>Entered Value</th>
                    <th style={{ textAlign: 'left', padding: '0.4rem 0' }}>Reference Interval</th>
                    <th style={{ textAlign: 'right', padding: '0.4rem 0' }}>Flag</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedOrder.items.map((item) => (
                    <tr key={item.id} style={{ borderBottom: '1px solid var(--secondary-100)' }}>
                      <td style={{ padding: '0.5rem 0', fontWeight: 600 }}>{item.test.test_name}</td>
                      <td style={{ padding: '0.5rem 0' }}>{item.result?.numeric_value ?? item.result?.text_value ?? 'N/A'} {item.result?.unit || ''}</td>
                      <td style={{ padding: '0.5rem 0', color: 'var(--secondary-500)' }}>{item.result?.reference_range || '-'}</td>
                      <td style={{ padding: '0.5rem 0', textAlign: 'right' }}>
                        <Badge variant={item.result?.is_critical ? 'rose' : item.result?.result_flag === 'NORMAL' ? 'green' : 'amber'}>
                          {item.result?.result_flag}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <form onSubmit={handleSubmitVerify} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Verification Sign-off Notes
                </label>
                <textarea
                  rows={2}
                  value={verificationNotes}
                  onChange={(e) => setVerificationNotes(e.target.value)}
                  placeholder="Confirm quality control check, analyzer calibration, and verification sign-off..."
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                <Button variant="ghost" type="button" onClick={() => setActiveModal(null)}>Cancel</Button>
                <Button variant="primary" type="submit" disabled={actionLoading} style={{ background: '#0d9488' }}>
                  {actionLoading ? 'Verifying...' : 'Sign & Verify Results'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODAL 4: ORDER DETAILS & AUDIT TIMELINE */}
      {/* ------------------------------------------------------------- */}
      {activeModal === 'DETAIL' && selectedOrder && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '680px', width: '100%', maxHeight: '85vh', display: 'flex', flexDirection: 'column', boxShadow: 'var(--shadow-lg)', overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.75rem', borderBottom: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
                  Order Details #{selectedOrder.id}
                </h3>
                <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                  Ordered on {new Date(selectedOrder.ordered_at).toLocaleString()}
                </span>
              </div>
              <button type="button" onClick={() => setActiveModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '1.5rem 1.75rem', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Order Info Summary */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem', background: 'var(--bg-main)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Patient</div>
                  <div style={{ fontWeight: 700 }}>{selectedOrder.patient_name}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Doctor</div>
                  <div style={{ fontWeight: 700 }}>{selectedOrder.doctor_name}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Priority</div>
                  <div>{getPriorityBadge(selectedOrder.priority)}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Status</div>
                  <div>{getStatusBadge(selectedOrder.status)}</div>
                </div>
              </div>

              {/* Audit Timeline */}
              <div>
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: '0.75rem' }}>Lifecycle Audit Trail</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {(selectedOrder.audit_events || []).map((ev) => (
                    <div key={ev.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', fontSize: '0.8125rem', padding: '0.5rem 0', borderBottom: '1px solid var(--secondary-100)' }}>
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#7c3aed', marginTop: '6px', flexShrink: 0 }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 700, color: 'var(--secondary-900)' }}>{ev.action} • {ev.performed_by_name}</div>
                        <div style={{ color: 'var(--secondary-600)', marginTop: '2px' }}>{ev.details}</div>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--secondary-400)' }}>
                        {new Date(ev.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ padding: '1rem 1.75rem', borderTop: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="primary" onClick={() => setActiveModal(null)}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LabDashboardPage;
