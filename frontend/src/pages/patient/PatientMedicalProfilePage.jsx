import React, { useState, useEffect } from 'react';
import {
  User,
  HeartPulse,
  AlertOctagon,
  Pill,
  Shield,
  Activity,
  Plus,
  Trash2,
  Save,
  CheckCircle,
  AlertCircle,
  Phone,
  Calendar,
  Sparkles,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import patientService from '../../services/patientService';

const DEFAULT_ALLERGY_ROW = {
  name: '',
  type: 'MEDICATION',
  severity: 'MODERATE',
  reaction: '',
};

const DEFAULT_MEDICATION_ROW = {
  name: '',
  dosage: '',
  frequency: '',
  instructions: '',
};

export function PatientMedicalProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Form State
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gender, setGender] = useState('');
  const [bloodGroup, setBloodGroup] = useState('');
  const [allergies, setAllergies] = useState([]);
  const [chronicConditions, setChronicConditions] = useState([]);
  const [newChronicCondition, setNewChronicCondition] = useState('');
  const [pastConditions, setPastConditions] = useState([]);
  const [newPastCondition, setNewPastCondition] = useState('');
  const [surgeries, setSurgeries] = useState([]);
  const [newSurgery, setNewSurgery] = useState('');
  const [currentMedications, setCurrentMedications] = useState([]);
  const [smokingStatus, setSmokingStatus] = useState('');
  const [alcoholConsumption, setAlcoholConsumption] = useState('');
  const [emergencyContactName, setEmergencyContactName] = useState('');
  const [emergencyContactPhone, setEmergencyContactPhone] = useState('');
  const [emergencyContactRelationship, setEmergencyContactRelationship] = useState('');
  const [medicalHistorySummary, setMedicalHistorySummary] = useState('');

  useEffect(() => {
    loadMedicalProfile();
  }, []);

  const loadMedicalProfile = async () => {
    try {
      setLoading(true);
      const data = await patientService.getMedicalProfile();
      if (data) {
        setDateOfBirth(data.date_of_birth || '');
        setGender(data.gender || '');
        setBloodGroup(data.blood_group || '');
        setAllergies(Array.isArray(data.allergies) ? data.allergies : []);
        setChronicConditions(Array.isArray(data.chronic_conditions) ? data.chronic_conditions : []);
        setPastConditions(Array.isArray(data.past_conditions) ? data.past_conditions : []);
        setSurgeries(Array.isArray(data.surgeries) ? data.surgeries : []);
        setCurrentMedications(Array.isArray(data.current_medications) ? data.current_medications : []);
        setSmokingStatus(data.smoking_status || '');
        setAlcoholConsumption(data.alcohol_consumption || '');
        setEmergencyContactName(data.emergency_contact_name || '');
        setEmergencyContactPhone(data.emergency_contact_phone || '');
        setEmergencyContactRelationship(data.emergency_contact_relationship || '');
        setMedicalHistorySummary(data.medical_history_summary || '');
      }
    } catch (err) {
      console.error('Failed to load medical profile:', err);
      setErrorMessage('Failed to load your medical profile.');
    } finally {
      setLoading(false);
    }
  };

  // Allergy handlers
  const handleAddAllergy = () => {
    setAllergies([...allergies, { ...DEFAULT_ALLERGY_ROW }]);
  };

  const handleRemoveAllergy = (index) => {
    setAllergies(allergies.filter((_, i) => i !== index));
  };

  const handleAllergyChange = (index, field, value) => {
    const updated = [...allergies];
    updated[index][field] = value;
    setAllergies(updated);
  };

  // Medication handlers
  const handleAddMedication = () => {
    setCurrentMedications([...currentMedications, { ...DEFAULT_MEDICATION_ROW }]);
  };

  const handleRemoveMedication = (index) => {
    setCurrentMedications(currentMedications.filter((_, i) => i !== index));
  };

  const handleMedicationChange = (index, field, value) => {
    const updated = [...currentMedications];
    updated[index][field] = value;
    setCurrentMedications(updated);
  };

  // Condition handlers
  const handleAddChronicCondition = () => {
    if (newChronicCondition.trim()) {
      setChronicConditions([...chronicConditions, newChronicCondition.trim()]);
      setNewChronicCondition('');
    }
  };

  const handleRemoveChronicCondition = (index) => {
    setChronicConditions(chronicConditions.filter((_, i) => i !== index));
  };

  const handleAddPastCondition = () => {
    if (newPastCondition.trim()) {
      setPastConditions([...pastConditions, newPastCondition.trim()]);
      setNewPastCondition('');
    }
  };

  const handleRemovePastCondition = (index) => {
    setPastConditions(pastConditions.filter((_, i) => i !== index));
  };

  const handleAddSurgery = () => {
    if (newSurgery.trim()) {
      setSurgeries([...surgeries, newSurgery.trim()]);
      setNewSurgery('');
    }
  };

  const handleRemoveSurgery = (index) => {
    setSurgeries(surgeries.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      setSuccessMessage(null);
      setErrorMessage(null);

      // Clean allergies
      const cleanAllergies = allergies
        .filter((a) => a.name && a.name.trim().length > 0)
        .map((a) => ({
          name: a.name.trim(),
          type: a.type || 'MEDICATION',
          severity: a.severity || 'MODERATE',
          reaction: a.reaction?.trim() || null,
        }));

      // Clean medications
      const cleanMedications = currentMedications
        .filter((m) => m.name && m.name.trim().length > 0)
        .map((m) => ({
          name: m.name.trim(),
          dosage: m.dosage?.trim() || null,
          frequency: m.frequency?.trim() || null,
          instructions: m.instructions?.trim() || null,
        }));

      const payload = {
        date_of_birth: dateOfBirth || null,
        gender: gender || null,
        blood_group: bloodGroup || null,
        allergies: cleanAllergies,
        chronic_conditions: chronicConditions,
        past_conditions: pastConditions,
        surgeries: surgeries,
        current_medications: cleanMedications,
        smoking_status: smokingStatus || null,
        alcohol_consumption: alcoholConsumption || null,
        emergency_contact_name: emergencyContactName.trim() || null,
        emergency_contact_phone: emergencyContactPhone.trim() || null,
        emergency_contact_relationship: emergencyContactRelationship.trim() || null,
        medical_history_summary: medicalHistorySummary.trim() || null,
      };

      await patientService.updateMedicalProfile(payload);
      setSuccessMessage('Medical profile and health history saved successfully.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      console.error('Failed to save medical profile:', err);
      setErrorMessage(err.message || 'Failed to update medical profile.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
        Loading patient medical profile...
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ maxWidth: '960px', margin: '0 auto', paddingBottom: '3rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
          <HeartPulse size={28} color="var(--primary-700)" />
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800 }}>Patient Medical Profile</h1>
        </div>
        <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
          Maintain your clinical health record, known drug/food allergies, active medications, and emergency contacts for physician consultations and AI safety audits.
        </p>
      </div>

      {successMessage && (
        <div
          style={{
            background: '#dcfce7',
            border: '1px solid #bbf7d0',
            color: '#15803d',
            padding: '0.875rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <CheckCircle size={18} />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div
          style={{
            background: '#fff1f2',
            border: '1px solid #fecdd3',
            color: '#9f1239',
            padding: '0.875rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Section 1: Basic Health Information */}
        <Card title="1. Basic Health & Demographic Information" subtitle="Primary biological vitals and demographics">
          <div className="grid grid-cols-3 gap-4">
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Date of Birth</label>
              <input
                type="date"
                className="form-input"
                value={dateOfBirth}
                onChange={(e) => setDateOfBirth(e.target.value)}
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Gender</label>
              <select
                className="form-input"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
              >
                <option value="">Select Gender</option>
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Non-Binary">Non-Binary</option>
                <option value="Other">Other / Prefer not to specify</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Blood Group</label>
              <select
                className="form-input"
                value={bloodGroup}
                onChange={(e) => setBloodGroup(e.target.value)}
              >
                <option value="">Select Blood Group</option>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Section 2: Allergies & Hypersensitivities */}
        <Card
          title="2. Allergies & Clinical Hypersensitivities"
          subtitle="Medications, foods, or environmental triggers audited during AI prescription safety analysis"
        >
          <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-600)' }}>
              Total recorded allergies: <strong>{allergies.length}</strong>
            </span>
            <Button
              type="button"
              variant="secondary"
              icon={Plus}
              style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
              onClick={handleAddAllergy}
            >
              Add Allergy
            </Button>
          </div>

          {allergies.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '1.5rem', background: '#f8fafc', borderRadius: '8px', border: '1px dashed var(--secondary-200)' }}>
              <p style={{ color: 'var(--secondary-500)', fontSize: '0.8125rem', margin: 0 }}>
                No allergies recorded. Click "Add Allergy" if you have known reactions to antibiotics, NSAIDs, sulfa drugs, or foods.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {allergies.map((allergy, idx) => (
                <div
                  key={idx}
                  style={{
                    background: '#ffffff',
                    border: '1px solid var(--secondary-200)',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.875rem',
                    display: 'grid',
                    gridTemplateColumns: '2fr 1.2fr 1fr 2fr auto',
                    gap: '0.75rem',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <label style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                      Allergen Name *
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      style={{ fontSize: '0.8125rem', padding: '0.4rem 0.5rem' }}
                      placeholder="e.g. Penicillin, Aspirin, Peanuts"
                      value={allergy.name}
                      onChange={(e) => handleAllergyChange(idx, 'name', e.target.value)}
                      required
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                      Type
                    </label>
                    <select
                      className="form-input"
                      style={{ fontSize: '0.8125rem', padding: '0.4rem 0.5rem' }}
                      value={allergy.type}
                      onChange={(e) => handleAllergyChange(idx, 'type', e.target.value)}
                    >
                      <option value="MEDICATION">Medication</option>
                      <option value="FOOD">Food</option>
                      <option value="ENVIRONMENTAL">Environmental</option>
                      <option value="OTHER">Other</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                      Severity
                    </label>
                    <select
                      className="form-input"
                      style={{ fontSize: '0.8125rem', padding: '0.4rem 0.5rem' }}
                      value={allergy.severity}
                      onChange={(e) => handleAllergyChange(idx, 'severity', e.target.value)}
                    >
                      <option value="CRITICAL">Critical</option>
                      <option value="HIGH">High</option>
                      <option value="MODERATE">Moderate</option>
                      <option value="LOW">Low</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                      Observed Reaction
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      style={{ fontSize: '0.8125rem', padding: '0.4rem 0.5rem' }}
                      placeholder="e.g. Rash, Anaphylaxis, Dyspnea"
                      value={allergy.reaction || ''}
                      onChange={(e) => handleAllergyChange(idx, 'reaction', e.target.value)}
                    />
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveAllergy(idx)}
                    style={{ background: 'none', border: 'none', color: 'var(--accent-rose)', cursor: 'pointer', padding: '6px', marginTop: '14px' }}
                    title="Remove Allergy"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Section 3: Medical Conditions & Surgeries */}
        <Card title="3. Medical Conditions & Surgical History" subtitle="Active chronic illnesses, past resolved conditions, and prior operations">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Chronic Conditions */}
            <div>
              <label className="form-label" style={{ marginBottom: '4px' }}>Active Chronic Conditions</label>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Hypertension, Type 2 Diabetes, Asthma"
                  value={newChronicCondition}
                  onChange={(e) => setNewChronicCondition(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddChronicCondition();
                    }
                  }}
                />
                <Button type="button" variant="secondary" onClick={handleAddChronicCondition}>
                  Add
                </Button>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {chronicConditions.map((cond, i) => (
                  <span
                    key={i}
                    style={{
                      background: 'var(--primary-50)',
                      color: 'var(--primary-800)',
                      border: '1px solid var(--primary-200)',
                      borderRadius: '20px',
                      padding: '0.25rem 0.75rem',
                      fontSize: '0.8125rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    {cond}
                    <button
                      type="button"
                      onClick={() => handleRemoveChronicCondition(i)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary-700)', padding: 0, lineHeight: 1 }}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Past Conditions */}
            <div>
              <label className="form-label" style={{ marginBottom: '4px' }}>Past Resolved Conditions</label>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Pneumonia (2021), Hepatitis A"
                  value={newPastCondition}
                  onChange={(e) => setNewPastCondition(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddPastCondition();
                    }
                  }}
                />
                <Button type="button" variant="secondary" onClick={handleAddPastCondition}>
                  Add
                </Button>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {pastConditions.map((cond, i) => (
                  <span
                    key={i}
                    style={{
                      background: '#f8fafc',
                      color: 'var(--secondary-700)',
                      border: '1px solid var(--secondary-200)',
                      borderRadius: '20px',
                      padding: '0.25rem 0.75rem',
                      fontSize: '0.8125rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    {cond}
                    <button
                      type="button"
                      onClick={() => handleRemovePastCondition(i)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)', padding: 0 }}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Surgical History */}
            <div>
              <label className="form-label" style={{ marginBottom: '4px' }}>Past Surgical Procedures</label>
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Appendectomy (2016), Knee Arthroscopy (2020)"
                  value={newSurgery}
                  onChange={(e) => setNewSurgery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddSurgery();
                    }
                  }}
                />
                <Button type="button" variant="secondary" onClick={handleAddSurgery}>
                  Add
                </Button>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {surgeries.map((surg, i) => (
                  <span
                    key={i}
                    style={{
                      background: '#f8fafc',
                      color: 'var(--secondary-700)',
                      border: '1px solid var(--secondary-200)',
                      borderRadius: '20px',
                      padding: '0.25rem 0.75rem',
                      fontSize: '0.8125rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    {surg}
                    <button
                      type="button"
                      onClick={() => handleRemoveSurgery(i)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)', padding: 0 }}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* Section 4: Current Medications */}
        <Card
          title="4. Current Active Medications"
          subtitle="Medications and supplements you take regularly"
        >
          <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-600)' }}>
              Active medications: <strong>{currentMedications.length}</strong>
            </span>
            <Button
              type="button"
              variant="secondary"
              icon={Plus}
              style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
              onClick={handleAddMedication}
            >
              Add Current Medication
            </Button>
          </div>

          {currentMedications.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '1.5rem', background: '#f8fafc', borderRadius: '8px', border: '1px dashed var(--secondary-200)' }}>
              <p style={{ color: 'var(--secondary-500)', fontSize: '0.8125rem', margin: 0 }}>
                No active daily medications recorded.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {currentMedications.map((med, idx) => (
                <div
                  key={idx}
                  style={{
                    background: '#ffffff',
                    border: '1px solid var(--secondary-200)',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.875rem',
                    display: 'grid',
                    gridTemplateColumns: '2fr 1fr 1.2fr 2fr auto',
                    gap: '0.75rem',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <label style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                      Medication Name *
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      style={{ fontSize: '0.8125rem', padding: '0.4rem 0.5rem' }}
                      placeholder="e.g. Metformin, Lisinopril"
                      value={med.name}
                      onChange={(e) => handleMedicationChange(idx, 'name', e.target.value)}
                      required
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                      Dosage
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      style={{ fontSize: '0.8125rem', padding: '0.4rem 0.5rem' }}
                      placeholder="e.g. 500 mg"
                      value={med.dosage || ''}
                      onChange={(e) => handleMedicationChange(idx, 'dosage', e.target.value)}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                      Frequency
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      style={{ fontSize: '0.8125rem', padding: '0.4rem 0.5rem' }}
                      placeholder="e.g. Twice daily"
                      value={med.frequency || ''}
                      onChange={(e) => handleMedicationChange(idx, 'frequency', e.target.value)}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', display: 'block', marginBottom: '2px' }}>
                      Instructions
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      style={{ fontSize: '0.8125rem', padding: '0.4rem 0.5rem' }}
                      placeholder="e.g. Take with meals"
                      value={med.instructions || ''}
                      onChange={(e) => handleMedicationChange(idx, 'instructions', e.target.value)}
                    />
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveMedication(idx)}
                    style={{ background: 'none', border: 'none', color: 'var(--accent-rose)', cursor: 'pointer', padding: '6px', marginTop: '14px' }}
                    title="Remove Medication"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Section 5: Lifestyle & Habits */}
        <Card title="5. Lifestyle & Social History" subtitle="Social habits relevant to cardiovascular and metabolic care">
          <div className="grid grid-cols-2 gap-4">
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Smoking Status</label>
              <select
                className="form-input"
                value={smokingStatus}
                onChange={(e) => setSmokingStatus(e.target.value)}
              >
                <option value="">Select Smoking Status</option>
                <option value="NEVER">Never Smoked</option>
                <option value="FORMER">Former Smoker (Quit)</option>
                <option value="OCCASIONAL">Occasional / Social</option>
                <option value="CURRENT">Current Smoker</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Alcohol Consumption</label>
              <select
                className="form-input"
                value={alcoholConsumption}
                onChange={(e) => setAlcoholConsumption(e.target.value)}
              >
                <option value="">Select Alcohol Consumption</option>
                <option value="NONE">None / Abstinent</option>
                <option value="OCCASIONAL">Occasional / Social</option>
                <option value="MODERATE">Moderate (1-2 drinks/day)</option>
                <option value="HEAVY">Heavy / Frequent</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Section 6: Emergency Contact Information */}
        <Card title="6. Emergency Contact Information" subtitle="Primary emergency contact in case of clinical urgent notifications">
          <div className="grid grid-cols-3 gap-4">
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Contact Full Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Jane Doe"
                value={emergencyContactName}
                onChange={(e) => setEmergencyContactName(e.target.value)}
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Phone Number</label>
              <input
                type="tel"
                className="form-input"
                placeholder="e.g. +1-555-0199"
                value={emergencyContactPhone}
                onChange={(e) => setEmergencyContactPhone(e.target.value)}
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Relationship</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Spouse, Parent, Sibling"
                value={emergencyContactRelationship}
                onChange={(e) => setEmergencyContactRelationship(e.target.value)}
              />
            </div>
          </div>
        </Card>

        {/* Clinical History Summary */}
        <Card title="7. Clinical History Summary & Notes" subtitle="Additional health observations or provider notes">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <textarea
              className="form-input"
              rows={3}
              placeholder="e.g. Patient has a family history of coronary artery disease. Under regular cardiology review."
              value={medicalHistorySummary}
              onChange={(e) => setMedicalHistorySummary(e.target.value)}
            />
          </div>
        </Card>

        {/* Save Bar */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '0.5rem' }}>
          <Button
            type="submit"
            variant="primary"
            icon={Save}
            disabled={saving}
            style={{ padding: '0.75rem 2rem', fontSize: '0.9375rem' }}
          >
            {saving ? 'Saving Medical Profile...' : 'Save & Update Medical Profile'}
          </Button>
        </div>
      </form>
    </div>
  );
}

export default PatientMedicalProfilePage;
