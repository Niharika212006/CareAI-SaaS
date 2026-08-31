import React, { useState, useEffect, useCallback } from 'react';
import {
  FlaskConical,
  Plus,
  Search,
  Filter,
  RefreshCw,
  Clock,
  CheckCircle,
  AlertTriangle,
  FileText,
  User,
  ShieldCheck,
  X,
  Stethoscope,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import labService from '../../services/labService';
import appointmentService from '../../services/appointmentService';

export function DoctorLabOrdersPage() {
  const { user } = useAuth();

  const [orders, setOrders] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // New Order Modal State
  const [isOrderModalOpen, setIsOrderModalOpen] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [orderPriority, setOrderPriority] = useState('ROUTINE');
  const [clinicalNotes, setClinicalNotes] = useState('');
  const [selectedTestIds, setSelectedTestIds] = useState([]);
  const [catalogSearch, setCatalogSearch] = useState('');
  const [catalogCategory, setCatalogCategory] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // Order Details Modal State
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [ordersRes, catalogRes, apptsRes] = await Promise.all([
        labService.getDoctorOrders(),
        labService.getTests({ active_only: true }),
        appointmentService.getDoctorAppointments ? appointmentService.getDoctorAppointments() : Promise.resolve([]),
      ]);

      setOrders(ordersRes || []);
      setCatalog(catalogRes || []);

      // Extract unique related patients from appointments
      const patientMap = new Map();
      (apptsRes || []).forEach((appt) => {
        if (appt.patient && appt.patient_id) {
          const name = appt.patient.user?.full_name || `Patient #${appt.patient_id}`;
          patientMap.set(appt.patient_id, { id: appt.patient_id, name });
        }
      });
      setPatients(Array.from(patientMap.values()));
    } catch (err) {
      setError(err.message || 'Failed to load doctor laboratory requisitions.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleToggleTestSelect = (testId) => {
    setSelectedTestIds((prev) =>
      prev.includes(testId) ? prev.filter((id) => id !== testId) : [...prev, testId]
    );
  };

  const handleCreateOrder = async (e) => {
    e.preventDefault();
    if (!selectedPatientId) {
      setSubmitError('Please select or specify a target patient.');
      return;
    }
    if (selectedTestIds.length === 0) {
      setSubmitError('Please select at least one laboratory test to order.');
      return;
    }

    try {
      setSubmitting(true);
      setSubmitError(null);

      const payload = {
        patient_id: parseInt(selectedPatientId, 10),
        priority: orderPriority,
        clinical_notes: clinicalNotes,
        items: selectedTestIds.map((id) => ({ lab_test_id: id })),
      };

      await labService.createOrder(payload);
      setIsOrderModalOpen(false);
      // Reset form
      setSelectedPatientId('');
      setOrderPriority('ROUTINE');
      setClinicalNotes('');
      setSelectedTestIds([]);
      await loadData();
    } catch (err) {
      setSubmitError(err.message || 'Failed to submit laboratory order.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenDetail = async (orderId) => {
    try {
      const order = await labService.getOrder(orderId);
      setSelectedOrder(order);
      setDetailModalOpen(true);
    } catch (err) {
      alert(err.message || 'Failed to load order details.');
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'STAT':
        return <Badge variant="rose">STAT</Badge>;
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

  const filteredCatalog = catalog.filter((test) => {
    const matchesSearch =
      !catalogSearch ||
      test.test_name.toLowerCase().includes(catalogSearch.toLowerCase()) ||
      test.test_code.toLowerCase().includes(catalogSearch.toLowerCase());
    const matchesCat = !catalogCategory || test.category === catalogCategory;
    return matchesSearch && matchesCat;
  });

  const categories = Array.from(new Set(catalog.map((t) => t.category))).filter(Boolean);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #4f46e5 0%, #0284c7 100%)',
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
            <Badge variant="blue" style={{ background: '#ffffff', color: '#4f46e5', fontWeight: 700 }}>
              Clinical Diagnostic Requisitions
            </Badge>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0.25rem 0' }}>
            Doctor Laboratory Order Console
          </h1>
          <p style={{ color: 'rgba(255, 255, 255, 0.85)', margin: 0, fontSize: '0.9375rem' }}>
            Order diagnostic testing for your patients, track laboratory turnaround, and review released reports.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsOrderModalOpen(true)}
          style={{ background: '#ffffff', color: '#4f46e5', borderColor: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700 }}
        >
          <Plus size={16} /> Order Diagnostic Test
        </Button>
      </div>

      {/* Orders List Card */}
      <Card className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Stethoscope size={20} color="#4f46e5" /> My Authored Laboratory Requisitions
          </h3>
          <Button variant="ghost" size="sm" onClick={loadData} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </Button>
        </div>

        {error && (
          <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
            <AlertTriangle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} /> {error}
          </div>
        )}

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <div>Loading your lab requisitions...</div>
          </div>
        ) : orders.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <FlaskConical size={36} style={{ margin: '0 auto 0.75rem auto', opacity: 0.4 }} />
            <div style={{ fontWeight: 600 }}>No laboratory orders found.</div>
            <p style={{ fontSize: '0.8125rem', marginTop: '0.25rem' }}>Use the button above to order diagnostic tests for your patients.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--secondary-200)', color: 'var(--secondary-600)', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Order ID</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Patient</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Priority</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Ordered Tests</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Date Placed</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id} style={{ borderBottom: '1px solid var(--secondary-100)' }}>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700 }}>#{order.id}</td>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 600 }}>{order.patient_name}</td>
                    <td style={{ padding: '0.875rem 1rem' }}>{getPriorityBadge(order.priority)}</td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        {order.test_names.slice(0, 2).map((t, idx) => (
                          <span key={idx} style={{ fontSize: '0.8125rem' }}>• {t}</span>
                        ))}
                        {order.test_names.length > 2 && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>+{order.test_names.length - 2} more</span>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: 'var(--secondary-600)' }}>
                      {new Date(order.ordered_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                        {getStatusBadge(order.status)}
                        {order.is_critical_flagged && (
                          <Badge variant="rose">CRITICAL ALERT</Badge>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleOpenDetail(order.id)}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem' }}
                      >
                        <FileText size={14} /> View Report
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ------------------------------------------------------------- */}
      {/* MODAL: ORDER NEW DIAGNOSTIC TESTS */}
      {/* ------------------------------------------------------------- */}
      {isOrderModalOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '840px', width: '100%', maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: 'var(--shadow-lg)', overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.75rem', borderBottom: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FlaskConical size={20} color="#4f46e5" /> New Laboratory Diagnostic Requisition
                </h3>
                <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                  Requisition must be for a patient with an active clinical consultation relationship.
                </span>
              </div>
              <button type="button" onClick={() => setIsOrderModalOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '1.5rem 1.75rem', overflowY: 'auto', flex: 1 }}>
              {submitError && (
                <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.8125rem' }}>
                  {submitError}
                </div>
              )}

              <form id="doctor-order-form" onSubmit={handleCreateOrder} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {/* Patient & Priority Selectors */}
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.375rem' }}>
                      Target Patient *
                    </label>
                    {patients.length > 0 ? (
                      <select
                        required
                        value={selectedPatientId}
                        onChange={(e) => setSelectedPatientId(e.target.value)}
                        style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                      >
                        <option value="">Select Related Patient...</option>
                        {patients.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} (ID: #{p.id})
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="number"
                        required
                        placeholder="Enter Patient Profile ID..."
                        value={selectedPatientId}
                        onChange={(e) => setSelectedPatientId(e.target.value)}
                        style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                      />
                    )}
                  </div>

                  <div>
                    <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.375rem' }}>
                      Requisition Priority *
                    </label>
                    <select
                      value={orderPriority}
                      onChange={(e) => setOrderPriority(e.target.value)}
                      style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                    >
                      <option value="ROUTINE">ROUTINE (Standard turnaround)</option>
                      <option value="URGENT">URGENT (Expedited processing)</option>
                      <option value="STAT">STAT (Immediate life-critical draw)</option>
                    </select>
                  </div>
                </div>

                {/* Clinical Notes */}
                <div>
                  <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.375rem' }}>
                    Clinical Indication / Diagnosis Notes
                  </label>
                  <textarea
                    rows={2}
                    value={clinicalNotes}
                    onChange={(e) => setClinicalNotes(e.target.value)}
                    placeholder="Provide diagnostic indications, symptoms, or relevant medication context..."
                    style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                  />
                </div>

                {/* Diagnostic Test Catalog Picker */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <label style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--secondary-900)' }}>
                      Select Laboratory Tests ({selectedTestIds.length} selected)
                    </label>

                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <input
                        type="text"
                        placeholder="Search tests..."
                        value={catalogSearch}
                        onChange={(e) => setCatalogSearch(e.target.value)}
                        style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem', borderRadius: '6px', border: '1px solid var(--secondary-200)' }}
                      />
                      <select
                        value={catalogCategory}
                        onChange={(e) => setCatalogCategory(e.target.value)}
                        style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem', borderRadius: '6px', border: '1px solid var(--secondary-200)' }}
                      >
                        <option value="">All Categories</option>
                        {categories.map((c) => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div style={{ maxHeight: '240px', overflowY: 'auto', border: '1px solid var(--secondary-200)', borderRadius: 'var(--radius-md)', padding: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                    {filteredCatalog.map((test) => {
                      const isSelected = selectedTestIds.includes(test.id);
                      return (
                        <div
                          key={test.id}
                          onClick={() => handleToggleTestSelect(test.id)}
                          style={{
                            padding: '0.625rem 0.75rem',
                            borderRadius: 'var(--radius-md)',
                            background: isSelected ? 'var(--primary-50)' : '#ffffff',
                            border: isSelected ? '1px solid var(--primary-500)' : '1px solid var(--secondary-200)',
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          <div>
                            <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: isSelected ? 'var(--primary-900)' : 'var(--secondary-900)' }}>
                              {test.test_name}
                            </div>
                            <div style={{ fontSize: '0.6875rem', color: 'var(--secondary-500)' }}>
                              Code: {test.test_code} • Specimen: {test.specimen_type} • Category: {test.category}
                            </div>
                          </div>
                          <Badge variant={isSelected ? 'teal' : 'secondary'}>
                            {isSelected ? 'Selected' : '+ Add'}
                          </Badge>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </form>
            </div>

            <div style={{ padding: '1rem 1.75rem', borderTop: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="ghost" type="button" onClick={() => setIsOrderModalOpen(false)}>Cancel</Button>
              <Button form="doctor-order-form" variant="primary" type="submit" disabled={submitting} style={{ background: '#4f46e5' }}>
                {submitting ? 'Placing Order...' : 'Submit Requisition'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODAL: VIEW REPORT DETAILS */}
      {/* ------------------------------------------------------------- */}
      {detailModalOpen && selectedOrder && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '720px', width: '100%', maxHeight: '85vh', display: 'flex', flexDirection: 'column', boxShadow: 'var(--shadow-lg)', overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.75rem', borderBottom: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
                  Diagnostic Report #{selectedOrder.id}
                </h3>
                <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                  Patient: {selectedOrder.patient_name} • Status: {selectedOrder.status}
                </span>
              </div>
              <button type="button" onClick={() => setDetailModalOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '1.5rem 1.75rem', overflowY: 'auto', flex: 1 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--secondary-200)', color: 'var(--secondary-600)', textAlign: 'left' }}>
                    <th style={{ padding: '0.5rem 0' }}>Test Name</th>
                    <th style={{ padding: '0.5rem 0' }}>Result Value</th>
                    <th style={{ padding: '0.5rem 0' }}>Reference Range</th>
                    <th style={{ padding: '0.5rem 0', textAlign: 'right' }}>Flag</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedOrder.items.map((item) => (
                    <tr key={item.id} style={{ borderBottom: '1px solid var(--secondary-100)' }}>
                      <td style={{ padding: '0.75rem 0', fontWeight: 600 }}>{item.test.test_name}</td>
                      <td style={{ padding: '0.75rem 0', fontWeight: 700, color: item.result?.is_critical ? '#e11d48' : 'inherit' }}>
                        {item.result ? `${item.result.numeric_value ?? item.result.text_value ?? '-'} ${item.result.unit || ''}` : 'Pending Testing'}
                      </td>
                      <td style={{ padding: '0.75rem 0', color: 'var(--secondary-500)' }}>
                        {item.result?.reference_range || item.test?.reference_range || '-'}
                      </td>
                      <td style={{ padding: '0.75rem 0', textAlign: 'right' }}>
                        {item.result ? (
                          <Badge variant={item.result.is_critical ? 'rose' : item.result.result_flag === 'NORMAL' ? 'green' : 'amber'}>
                            {item.result.result_flag}
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Pending</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ padding: '1rem 1.75rem', borderTop: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="primary" onClick={() => setDetailModalOpen(false)}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DoctorLabOrdersPage;
