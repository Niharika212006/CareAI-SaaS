import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  FlaskConical,
  Activity,
  CheckCircle,
  AlertTriangle,
  Clock,
  ArrowLeft,
  RefreshCw,
  User,
  Stethoscope,
  FileText,
  ShieldCheck,
  Send,
  AlertCircle,
  Sparkles,
  Check,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import labService from '../../services/labService';

export function LabTestDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form states for in-page actions
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Specimen Collection State
  const [specimenType, setSpecimenType] = useState('Whole Blood (EDTA)');
  const [sampleCondition, setSampleCondition] = useState('ACCEPTABLE');
  const [collectionNotes, setCollectionNotes] = useState('');

  // Result Entry State
  const [resultInputs, setResultInputs] = useState({});

  // Verification State
  const [verificationNotes, setVerificationNotes] = useState('');

  const loadOrderDetail = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await labService.getOrder(id);
      setOrder(res);

      // Initialize result inputs from existing results
      const initial = {};
      (res.items || []).forEach((item) => {
        initial[item.id] = {
          numeric_value: item.result?.numeric_value ?? '',
          text_value: item.result?.text_value ?? '',
          unit: item.result?.unit || item.test?.unit || '',
          reference_range: item.result?.reference_range || item.test?.reference_range || '',
        };
      });
      setResultInputs(initial);

      if (res.items?.[0]?.test?.specimen_type) {
        setSpecimenType(res.items[0].test.specimen_type);
      }
    } catch (err) {
      setError(err.message || `Failed to load lab order #${id}.`);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadOrderDetail();
  }, [loadOrderDetail]);

  // Action handlers
  const handleCollectSample = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      setActionError(null);
      await labService.collectSample(order.id, {
        specimen_type: specimenType,
        sample_condition: sampleCondition,
        collection_notes: collectionNotes,
      });
      setActionSuccess('Specimen collection recorded successfully.');
      await loadOrderDetail();
    } catch (err) {
      setActionError(err.message || 'Failed to record specimen collection.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartTesting = async () => {
    try {
      setActionLoading(true);
      setActionError(null);
      await labService.startProcessing(order.id);
      setActionSuccess('Laboratory testing commenced.');
      await loadOrderDetail();
    } catch (err) {
      setActionError(err.message || 'Failed to start testing.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveResults = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      setActionError(null);

      const batchResults = (order.items || []).map((item) => {
        const input = resultInputs[item.id] || {};
        return {
          lab_order_item_id: item.id,
          numeric_value: input.numeric_value !== '' ? parseFloat(input.numeric_value) : null,
          text_value: input.text_value || null,
          unit: input.unit || null,
          reference_range: input.reference_range || null,
        };
      });

      await labService.enterResults(order.id, { results: batchResults });
      setActionSuccess('Analytical results saved and flags evaluated.');
      await loadOrderDetail();
    } catch (err) {
      setActionError(err.message || 'Failed to enter results.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleVerifyResults = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      setActionError(null);
      await labService.verifyResults(order.id, verificationNotes);
      setActionSuccess('Diagnostic results verified successfully.');
      await loadOrderDetail();
    } catch (err) {
      setActionError(err.message || 'Failed to verify results.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReleaseReport = async () => {
    if (!window.confirm('Are you sure you want to release this verified report to the patient and ordering doctor?')) {
      return;
    }
    try {
      setActionLoading(true);
      setActionError(null);
      await labService.releaseResults(order.id);
      setActionSuccess('Diagnostic report released. Notifications dispatched to patient and physician.');
      await loadOrderDetail();
    } catch (err) {
      setActionError(err.message || 'Failed to release diagnostic report.');
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

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
        <Activity size={32} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#7c3aed' }} />
        <div>Loading Lab Requisition Workstation...</div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <Link to="/lab/tests" style={{ color: 'var(--secondary-500)', textDecoration: 'none', display: 'flex', alignItems: 'center' }}>
          <ArrowLeft size={16} style={{ marginRight: '0.25rem' }} /> Back to Work Queue
        </Link>
        <Card style={{ padding: '2rem', background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c' }}>
          <AlertTriangle size={24} style={{ marginBottom: '0.5rem' }} />
          <div style={{ fontWeight: 700 }}>{error || 'Requisition not found'}</div>
        </Card>
      </div>
    );
  }

  const steps = [
    { label: 'Requisition Ordered', completed: true },
    {
      label: 'Specimen Collected',
      completed: ['SAMPLE_COLLECTED', 'IN_PROGRESS', 'RESULTS_ENTERED', 'VERIFIED', 'RELEASED'].includes(order.status),
    },
    {
      label: 'Analytical Testing',
      completed: ['IN_PROGRESS', 'RESULTS_ENTERED', 'VERIFIED', 'RELEASED'].includes(order.status),
    },
    {
      label: 'Results Entered',
      completed: ['RESULTS_ENTERED', 'VERIFIED', 'RELEASED'].includes(order.status),
    },
    {
      label: 'Verified & Quality Checked',
      completed: ['VERIFIED', 'RELEASED'].includes(order.status),
    },
    {
      label: 'Released to Patient',
      completed: order.status === 'RELEASED',
    },
  ];

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Navigation & Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Link to="/lab/tests" style={{ color: 'var(--secondary-500)', textDecoration: 'none', display: 'flex', alignItems: 'center', fontSize: '0.875rem' }}>
            <ArrowLeft size={16} style={{ marginRight: '0.25rem' }} /> Requisitions
          </Link>
          <span style={{ color: 'var(--secondary-300)' }}>/</span>
          <span style={{ fontWeight: 700, color: 'var(--secondary-900)' }}>Requisition #{order.id}</span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={loadOrderDetail}
            disabled={actionLoading}
            style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}
          >
            <RefreshCw size={14} className={actionLoading ? 'animate-spin' : ''} /> Refresh
          </Button>
        </div>
      </div>

      {/* Patient-Safe Demographics & Order Requisition Banner */}
      <Card
        className="glass-panel"
        style={{
          padding: '1.5rem',
          background: 'linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%)',
          border: '1px solid #e9d5ff',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.375rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                Requisition #{order.id}
              </span>
              {getPriorityBadge(order.priority)}
              {getStatusBadge(order.status)}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <div style={{ background: '#ede9fe', padding: '0.5rem', borderRadius: '8px', color: '#7c3aed' }}>
                  <User size={18} />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Patient (Demographics)</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--secondary-900)' }}>{order.patient_name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-400)' }}>Patient ID #{order.patient_id}</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <div style={{ background: '#ede9fe', padding: '0.5rem', borderRadius: '8px', color: '#7c3aed' }}>
                  <Stethoscope size={18} />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Ordering Physician</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--secondary-900)' }}>{order.doctor_name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-400)' }}>Doctor ID #{order.doctor_id}</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <div style={{ background: '#ede9fe', padding: '0.5rem', borderRadius: '8px', color: '#7c3aed' }}>
                  <Clock size={18} />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Ordered Timestamp</div>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--secondary-800)' }}>
                    {order.ordered_at ? new Date(order.ordered_at).toLocaleString() : 'N/A'}
                  </div>
                </div>
              </div>
            </div>

            {order.clinical_notes && (
              <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.8125rem' }}>
                <strong style={{ color: 'var(--secondary-700)' }}>Clinical Indication / Physician Notes:</strong> {order.clinical_notes}
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Workflow Stepper */}
      <Card className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
          Diagnostic Lifecycle Pipeline
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          {steps.map((step, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                color: step.completed ? '#059669' : 'var(--secondary-400)',
              }}
            >
              <div
                style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: step.completed ? '#d1fae5' : 'var(--secondary-100)',
                  color: step.completed ? '#059669' : 'var(--secondary-400)',
                  fontSize: '0.6875rem',
                }}
              >
                {step.completed ? <Check size={12} /> : idx + 1}
              </div>
              <span>{step.label}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Status Action Feedback Messages */}
      {actionError && (
        <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '0.875rem 1rem', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
          <AlertCircle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} /> {actionError}
        </div>
      )}

      {actionSuccess && (
        <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#047857', padding: '0.875rem 1rem', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
          <CheckCircle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} /> {actionSuccess}
        </div>
      )}

      {/* SECTION 1: SPECIMEN COLLECTION WORKFLOW */}
      <Card className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FlaskConical size={20} color="#7c3aed" /> Biological Specimen Accessioning
          </h3>
          {(order.samples || []).length > 0 ? (
            <Badge variant="teal">Specimen Received</Badge>
          ) : (
            <Badge variant="amber">Collection Pending</Badge>
          )}
        </div>

        {(order.samples || []).length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {order.samples.map((sample) => (
              <div
                key={sample.id}
                style={{
                  padding: '1rem',
                  background: 'var(--bg-main)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--secondary-200)',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '1rem',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Specimen Type</div>
                  <div style={{ fontWeight: 700, color: 'var(--secondary-900)' }}>{sample.specimen_type}</div>
                </div>

                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Specimen Condition</div>
                  <Badge variant={sample.sample_condition === 'ACCEPTABLE' ? 'teal' : 'amber'}>
                    {sample.sample_condition}
                  </Badge>
                </div>

                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Collected By & Date</div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{sample.technician_name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-400)' }}>
                    {sample.collected_at ? new Date(sample.collected_at).toLocaleString() : ''}
                  </div>
                </div>

                {sample.collection_notes && (
                  <div style={{ gridColumn: '1 / -1', fontSize: '0.8125rem', color: 'var(--secondary-700)' }}>
                    <strong>Notes:</strong> {sample.collection_notes}
                  </div>
                )}
              </div>
            ))}

            {order.status === 'SAMPLE_COLLECTED' && (
              <div style={{ marginTop: '0.5rem', display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="primary"
                  onClick={handleStartTesting}
                  disabled={actionLoading}
                  style={{ background: '#7c3aed', borderColor: '#7c3aed' }}
                >
                  {actionLoading ? 'Starting...' : 'Commence Laboratory Testing'}
                </Button>
              </div>
            )}
          </div>
        ) : (
          <form onSubmit={handleCollectSample} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Specimen Type
                </label>
                <input
                  type="text"
                  required
                  value={specimenType}
                  onChange={(e) => setSpecimenType(e.target.value)}
                  placeholder="e.g. Whole Blood (EDTA)"
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
                  <option value="ACCEPTABLE">ACCEPTABLE (Integrity Verified)</option>
                  <option value="HEMOLYZED">HEMOLYZED (Recollection required)</option>
                  <option value="CLOTTED">CLOTTED (Recollection required)</option>
                  <option value="INSUFFICIENT">INSUFFICIENT (QNS)</option>
                  <option value="CONTAMINATED">CONTAMINATED</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                Collection Notes / Draw Observations
              </label>
              <input
                type="text"
                value={collectionNotes}
                onChange={(e) => setCollectionNotes(e.target.value)}
                placeholder="Venipuncture site, draw notes..."
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button type="submit" variant="primary" disabled={actionLoading} style={{ background: '#7c3aed' }}>
                {actionLoading ? 'Recording...' : 'Record Specimen Collection'}
              </Button>
            </div>
          </form>
        )}
      </Card>

      {/* SECTION 2: ANALYTICAL RESULTS & CLINICAL VALUES */}
      <Card className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={20} color="#0284c7" /> Diagnostic Test Items & Results
            </h3>
            <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
              Analytical values, reference intervals, and clinical alert flags.
            </span>
          </div>
        </div>

        <form onSubmit={handleSaveResults} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {(order.items || []).map((item) => {
            const input = resultInputs[item.id] || {};
            const isReleased = order.status === 'RELEASED';
            return (
              <Card key={item.id} style={{ padding: '1.25rem', border: '1px solid var(--secondary-200)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--secondary-900)' }}>
                      {item.test?.test_name || 'Diagnostic Test'}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                      Code: {item.test?.test_code || 'N/A'} • Category: {item.test?.category || 'General'}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <Badge variant="teal">
                      {item.test?.reference_range ? `Reference: ${item.test.reference_range} ${item.test.unit || ''}` : 'Qualitative'}
                    </Badge>
                    {item.result?.result_flag && item.result.result_flag !== 'NORMAL' && (
                      <Badge variant={item.result.result_flag === 'CRITICAL' ? 'rose' : 'amber'}>
                        {item.result.result_flag}
                      </Badge>
                    )}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--secondary-600)', display: 'block', marginBottom: '0.25rem' }}>
                      Numeric Value
                    </label>
                    <input
                      type="number"
                      step="any"
                      disabled={isReleased}
                      value={input.numeric_value}
                      onChange={(e) => {
                        const val = e.target.value;
                        setResultInputs((prev) => ({
                          ...prev,
                          [item.id]: { ...prev[item.id], numeric_value: val },
                        }));
                      }}
                      placeholder="e.g. 14.2"
                      style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--secondary-600)', display: 'block', marginBottom: '0.25rem' }}>
                      Qualitative Text (Optional)
                    </label>
                    <input
                      type="text"
                      disabled={isReleased}
                      value={input.text_value}
                      onChange={(e) => {
                        const val = e.target.value;
                        setResultInputs((prev) => ({
                          ...prev,
                          [item.id]: { ...prev[item.id], text_value: val },
                        }));
                      }}
                      placeholder="e.g. Negative, Reactive"
                      style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--secondary-600)', display: 'block', marginBottom: '0.25rem' }}>
                      Unit
                    </label>
                    <input
                      type="text"
                      disabled={isReleased}
                      value={input.unit}
                      onChange={(e) => {
                        const val = e.target.value;
                        setResultInputs((prev) => ({
                          ...prev,
                          [item.id]: { ...prev[item.id], unit: val },
                        }));
                      }}
                      placeholder="e.g. mg/dL"
                      style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                    />
                  </div>
                </div>

                {item.result && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.5rem', borderTop: '1px solid var(--secondary-100)', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--secondary-500)', flexWrap: 'wrap' }}>
                    <span>Entered by: {item.result.entered_by_name || 'Lab Staff'} ({item.result.entered_at ? new Date(item.result.entered_at).toLocaleTimeString() : ''})</span>
                    {item.result.verified_by_name && (
                      <span style={{ color: '#0d9488', fontWeight: 600 }}>Verified by: {item.result.verified_by_name}</span>
                    )}
                  </div>
                )}
              </Card>
            );
          })}

          {order.status !== 'RELEASED' && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
              <Button type="submit" variant="primary" disabled={actionLoading} style={{ background: '#0284c7' }}>
                {actionLoading ? 'Saving...' : 'Save Diagnostic Results'}
              </Button>
            </div>
          )}
        </form>
      </Card>

      {/* SECTION 3: VERIFICATION & RELEASE CONTROLS */}
      {(order.status === 'RESULTS_ENTERED' || order.status === 'VERIFIED') && (
        <Card className="glass-panel" style={{ padding: '1.5rem', border: '1px solid #99f6e4', background: '#f0fdfa' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0, color: '#0f766e', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <ShieldCheck size={20} color="#0f766e" /> Verification & Release Authority
              </h3>
              <p style={{ fontSize: '0.8125rem', color: '#115e59', margin: '0.25rem 0 0 0' }}>
                Quality control review, verification notes, and patient report release.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              {order.status === 'RESULTS_ENTERED' && (
                <Button
                  variant="primary"
                  onClick={handleVerifyResults}
                  disabled={actionLoading}
                  style={{ background: '#0d9488', borderColor: '#0d9488' }}
                >
                  <ShieldCheck size={16} style={{ marginRight: '0.375rem' }} /> Verify Results
                </Button>
              )}

              {order.status === 'VERIFIED' && (
                <Button
                  variant="primary"
                  onClick={handleReleaseReport}
                  disabled={actionLoading}
                  style={{ background: '#059669', borderColor: '#059669' }}
                >
                  <Send size={16} style={{ marginRight: '0.375rem' }} /> Release Report
                </Button>
              )}
            </div>
          </div>

          {order.status === 'RESULTS_ENTERED' && (
            <div>
              <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#134e4a', display: 'block', marginBottom: '0.25rem' }}>
                Verification Notes (Optional)
              </label>
              <textarea
                rows={2}
                value={verificationNotes}
                onChange={(e) => setVerificationNotes(e.target.value)}
                placeholder="Quality control confirmed. Values verified..."
                style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid #99f6e4', fontSize: '0.875rem' }}
              />
            </div>
          )}
        </Card>
      )}

      {/* SECTION 4: AUDIT LOG TIMELINE */}
      {(order.audit_events || []).length > 0 && (
        <Card className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 1rem 0', color: 'var(--secondary-900)' }}>
            Immutable Diagnostic Audit Trail
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {order.audit_events.map((event) => (
              <div
                key={event.id}
                style={{
                  padding: '0.75rem 1rem',
                  background: 'var(--bg-main)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--secondary-200)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.8125rem',
                }}
              >
                <div>
                  <strong style={{ color: 'var(--secondary-900)' }}>{event.action}</strong>
                  {event.details && <span style={{ color: 'var(--secondary-600)', marginLeft: '0.5rem' }}>— {event.details}</span>}
                </div>
                <div style={{ color: 'var(--secondary-500)', fontSize: '0.75rem' }}>
                  {event.performed_by_name} • {event.created_at ? new Date(event.created_at).toLocaleString() : ''}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

export default LabTestDetailPage;
