import React, { useState, useEffect, useCallback } from 'react';
import {
  FlaskConical,
  Plus,
  Search,
  Filter,
  RefreshCw,
  Edit2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Activity,
  Layers,
  X,
  ShieldCheck,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import labService from '../../services/labService';

export function AdminLabCatalogPage() {
  const [catalog, setCatalog] = useState([]);
  const [adminStats, setAdminStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search & Filter
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTest, setEditingTest] = useState(null);
  const [formData, setFormData] = useState({
    test_name: '',
    test_code: '',
    category: 'Hematology',
    specimen_type: 'Whole Blood (EDTA)',
    reference_range: '',
    unit: '',
    preparation_instructions: '',
    estimated_turnaround_time: '2-4 hours',
    is_active: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [testsRes, statsRes] = await Promise.all([
        labService.getTests({ active_only: false }),
        labService.getAdminStats(),
      ]);
      setCatalog(testsRes || []);
      setAdminStats(statsRes);
    } catch (err) {
      setError(err.message || 'Failed to load catalog or operational stats.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleOpenCreate = () => {
    setEditingTest(null);
    setFormData({
      test_name: '',
      test_code: '',
      category: 'Hematology',
      specimen_type: 'Whole Blood (EDTA)',
      reference_range: '',
      unit: '',
      preparation_instructions: '',
      estimated_turnaround_time: '2-4 hours',
      is_active: true,
    });
    setModalError(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (test) => {
    setEditingTest(test);
    setFormData({
      test_name: test.test_name,
      test_code: test.test_code,
      category: test.category,
      specimen_type: test.specimen_type,
      reference_range: test.reference_range || '',
      unit: test.unit || '',
      preparation_instructions: test.preparation_instructions || '',
      estimated_turnaround_time: test.estimated_turnaround_time || '',
      is_active: test.is_active,
    });
    setModalError(null);
    setIsModalOpen(true);
  };

  const handleToggleStatus = async (testId, currentStatus) => {
    try {
      await labService.toggleTestStatus(testId, !currentStatus);
      await loadData();
    } catch (err) {
      alert(err.message || 'Failed to update test status.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setModalError(null);

      if (editingTest) {
        await labService.updateTest(editingTest.id, formData);
      } else {
        await labService.createTest(formData);
      }

      setIsModalOpen(false);
      await loadData();
    } catch (err) {
      setModalError(err.message || 'Failed to save diagnostic test.');
    } finally {
      setSubmitting(false);
    }
  };

  const categories = Array.from(new Set(catalog.map((t) => t.category))).filter(Boolean);

  const filteredTests = catalog.filter((t) => {
    const matchesSearch =
      !search ||
      t.test_name.toLowerCase().includes(search.toLowerCase()) ||
      t.test_code.toLowerCase().includes(search.toLowerCase());
    const matchesCat = !categoryFilter || t.category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
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
            <Badge variant="secondary" style={{ background: '#ffffff', color: '#1e293b', fontWeight: 700 }}>
              Diagnostic Catalog Administration
            </Badge>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0.25rem 0' }}>
            Laboratory Test Catalog Management
          </h1>
          <p style={{ color: 'rgba(255, 255, 255, 0.85)', margin: 0, fontSize: '0.9375rem' }}>
            Configure diagnostic test codes, reference intervals, specimen preparation requirements, and monitor operational throughput.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={handleOpenCreate}
          style={{ background: 'var(--primary-600)', borderColor: 'var(--primary-600)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700 }}
        >
          <Plus size={16} /> Define New Lab Test
        </Button>
      </div>

      {/* Operational Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)', marginBottom: '0.25rem' }}>
            Active Tests in Catalog
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
            {adminStats?.active_test_catalog_count ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#0d9488', marginTop: '0.25rem' }}>Diagnostic catalog count</div>
        </Card>

        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)', marginBottom: '0.25rem' }}>
            Total Orders Logged
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
            {adminStats?.total_orders_all_time ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', marginTop: '0.25rem' }}>Platform lifetime</div>
        </Card>

        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)', marginBottom: '0.25rem' }}>
            Tests In Processing
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#7c3aed' }}>
            {adminStats?.tests_pending_processing ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#7c3aed', marginTop: '0.25rem' }}>Active lab workload</div>
        </Card>

        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)', marginBottom: '0.25rem' }}>
            Reports Released Today
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#059669' }}>
            {adminStats?.orders_completed_today ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#059669', marginTop: '0.25rem' }}>Daily published total</div>
        </Card>

        <Card className="glass-panel" style={{ padding: '1.25rem' }}>
          <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-500)', marginBottom: '0.25rem' }}>
            Critical Alert Audits
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#e11d48' }}>
            {adminStats?.total_critical_events ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#e11d48', marginTop: '0.25rem' }}>Panic value detections</div>
        </Card>
      </div>

      {/* Catalog Table Card */}
      <Card className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers size={20} color="var(--primary-600)" /> Standardized Diagnostic Test Catalog
          </h3>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <div style={{ position: 'relative', width: '220px' }}>
              <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--secondary-400)' }} />
              <input
                type="text"
                placeholder="Search catalog..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ width: '100%', padding: '0.45rem 0.75rem 0.45rem 2rem', fontSize: '0.8125rem', border: '1px solid var(--secondary-200)', borderRadius: 'var(--radius-md)' }}
              />
            </div>

            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              style={{ padding: '0.45rem 0.75rem', fontSize: '0.8125rem', border: '1px solid var(--secondary-200)', borderRadius: 'var(--radius-md)', background: '#ffffff' }}
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <div>Loading catalog definitions...</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--secondary-200)', color: 'var(--secondary-600)', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Test Code</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Test Name</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Category</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Specimen</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Reference Range</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTests.map((test) => (
                  <tr key={test.id} style={{ borderBottom: '1px solid var(--secondary-100)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: 'var(--primary-700)' }}>{test.test_code}</td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>{test.test_name}</td>
                    <td style={{ padding: '0.75rem 1rem' }}><Badge variant="teal">{test.category}</Badge></td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--secondary-600)' }}>{test.specimen_type}</td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--secondary-600)' }}>
                      {test.reference_range ? `${test.reference_range} ${test.unit || ''}` : 'Qualitative'}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <Badge variant={test.is_active ? 'green' : 'secondary'}>
                        {test.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.375rem' }}>
                        <Button size="sm" variant="ghost" onClick={() => handleOpenEdit(test)} title="Edit Test">
                          <Edit2 size={14} />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleToggleStatus(test.id, test.is_active)}
                          title={test.is_active ? 'Deactivate Test' : 'Activate Test'}
                          style={{ color: test.is_active ? '#e11d48' : '#059669' }}
                        >
                          {test.is_active ? <XCircle size={14} /> : <CheckCircle size={14} />}
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
      {/* MODAL: CREATE / EDIT LAB TEST */}
      {/* ------------------------------------------------------------- */}
      {isModalOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '640px', width: '100%', maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: 'var(--shadow-lg)', overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.75rem', borderBottom: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
                {editingTest ? 'Edit Diagnostic Test Definition' : 'Define New Diagnostic Test'}
              </h3>
              <button type="button" onClick={() => setIsModalOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '1.5rem 1.75rem', overflowY: 'auto', flex: 1 }}>
              {modalError && (
                <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.8125rem' }}>
                  {modalError}
                </div>
              )}

              <form id="lab-test-form" onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                      Test Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.test_name}
                      onChange={(e) => setFormData({ ...formData, test_name: e.target.value })}
                      placeholder="e.g. Complete Blood Count"
                      style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                      Test Code *
                    </label>
                    <input
                      type="text"
                      required
                      disabled={!!editingTest}
                      value={formData.test_code}
                      onChange={(e) => setFormData({ ...formData, test_code: e.target.value.toUpperCase() })}
                      placeholder="e.g. CBC-001"
                      style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                      Category *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                      placeholder="Hematology, Biochemistry, etc."
                      style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                      Specimen Type *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.specimen_type}
                      onChange={(e) => setFormData({ ...formData, specimen_type: e.target.value })}
                      placeholder="Whole Blood, Serum, Urine"
                      style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                      Reference Range
                    </label>
                    <input
                      type="text"
                      value={formData.reference_range}
                      onChange={(e) => setFormData({ ...formData, reference_range: e.target.value })}
                      placeholder="e.g. 70 - 99"
                      style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                      Measurement Unit
                    </label>
                    <input
                      type="text"
                      value={formData.unit}
                      onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                      placeholder="e.g. mg/dL, mmol/L"
                      style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                    Patient Preparation Instructions
                  </label>
                  <input
                    type="text"
                    value={formData.preparation_instructions}
                    onChange={(e) => setFormData({ ...formData, preparation_instructions: e.target.value })}
                    placeholder="e.g. Fasting 8-12 hours required prior to collection."
                    style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                  />
                </div>
              </form>
            </div>

            <div style={{ padding: '1rem 1.75rem', borderTop: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button variant="ghost" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
              <Button form="lab-test-form" variant="primary" type="submit" disabled={submitting}>
                {submitting ? 'Saving...' : editingTest ? 'Update Test' : 'Create Test'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminLabCatalogPage;
