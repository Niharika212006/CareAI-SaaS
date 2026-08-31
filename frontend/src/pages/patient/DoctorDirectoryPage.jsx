import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Stethoscope,
  Search,
  Calendar,
  Clock,
  DollarSign,
  Award,
  Building,
  CheckCircle,
  AlertCircle,
  X,
  Sparkles,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import useAuth from '../../hooks/useAuth';
import doctorService from '../../services/doctorService';
import appointmentService from '../../services/appointmentService';
import { formatCurrency } from '../../utils/formatters';

export function DoctorDirectoryPage() {
  const { isAuthenticated, isPatient } = useAuth();
  const navigate = useNavigate();

  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDoctor, setSelectedDoctor] = useState(null);

  // Booking Modal Form State
  const [bookingDate, setBookingDate] = useState('');
  const [bookingTime, setBookingTime] = useState('');
  const [availableSlots, setAvailableSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [reason, setReason] = useState('');
  const [patientNotes, setPatientNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState(null);
  const [bookingSuccess, setBookingSuccess] = useState(false);

  useEffect(() => {
    loadDoctors();
  }, []);

  // Fetch slots whenever selected doctor or booking date changes
  useEffect(() => {
    if (selectedDoctor && bookingDate) {
      loadSlots(selectedDoctor.id, bookingDate);
    }
  }, [selectedDoctor, bookingDate]);

  const loadDoctors = async (query = '') => {
    try {
      setLoading(true);
      const data = await doctorService.getDirectory(query);
      setDoctors(data || []);
    } catch (err) {
      console.error('Failed to load doctors directory:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSlots = async (docId, dateStr) => {
    try {
      setLoadingSlots(true);
      setBookingTime('');
      const res = await doctorService.getAvailableSlots(docId, dateStr);
      const slots = res.available_slots || [];
      setAvailableSlots(slots);
      if (slots.length > 0) {
        setBookingTime(slots[0]); // Select first slot by default
      }
    } catch (err) {
      console.error('Failed to load available slots:', err);
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadDoctors(searchTerm);
  };

  const openBookingModal = (doc) => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    if (!isPatient) {
      alert('Only registered patients can book consultations.');
      return;
    }
    setSelectedDoctor(doc);
    setBookingError(null);
    setBookingSuccess(false);

    // Default booking date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split('T')[0];
    setBookingDate(tomorrowStr);
    setReason('');
    setPatientNotes('');
  };

  const handleBookAppointment = async (e) => {
    e.preventDefault();
    if (!bookingDate || !bookingTime) {
      setBookingError('Please select both a consultation date and an available time slot.');
      return;
    }
    if (!reason.trim()) {
      setBookingError('Please enter a brief reason for the consultation.');
      return;
    }

    try {
      setSubmitting(true);
      setBookingError(null);

      // Combine date and time to ISO format safely
      const timeParts = bookingTime.split(':');
      const hours = parseInt(timeParts[0], 10) || 0;
      const minutes = parseInt(timeParts[1], 10) || 0;
      const [year, month, day] = bookingDate.split('-').map(Number);
      const scheduledStart = new Date(year, month - 1, day, hours, minutes, 0);

      if (isNaN(scheduledStart.getTime()) || scheduledStart <= new Date()) {
        setBookingError('Consultation time must be valid and scheduled in the future.');
        setSubmitting(false);
        return;
      }


      await appointmentService.createAppointment({
        doctor_id: selectedDoctor.id,
        scheduled_start: scheduledStart.toISOString(),
        reason: reason.trim(),
        patient_notes: patientNotes.trim() || undefined,
      });

      setBookingSuccess(true);
      setTimeout(() => {
        navigate('/patient/appointments');
      }, 1500);
    } catch (err) {
      console.error('Booking failed:', err);
      setBookingError(err.message || 'Failed to book appointment. Please choose another time slot.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page-container animate-fade-in" style={{ padding: '2rem 1.5rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <div style={{ background: 'var(--primary-100)', color: 'var(--primary-700)', padding: '0.5rem', borderRadius: '10px' }}>
            <Stethoscope size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.875rem', fontWeight: 800 }}>Verified Doctor Directory</h1>
            <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
              Discover approved medical specialists, check live consultation availability, and book verified appointments.
            </p>
          </div>
        </div>
      </div>

      {/* Search Filter Bar */}
      <Card style={{ marginBottom: '2rem' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 300px', position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--secondary-400)' }} />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '2.5rem' }}
              placeholder="Search by specialization (e.g. Cardiology, Neurology, Pediatrics)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button type="submit" variant="primary" icon={Search}>
            Search Doctors
          </Button>
          {searchTerm && (
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setSearchTerm('');
                loadDoctors('');
              }}
            >
              Clear Filter
            </Button>
          )}
        </form>
      </Card>

      {/* Doctor Cards Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--secondary-500)' }}>
          Loading certified practitioners...
        </div>
      ) : doctors.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: '3rem 1rem' }}>
          <Stethoscope size={40} color="var(--secondary-400)" style={{ marginBottom: '1rem' }} />
          <h3 style={{ fontSize: '1.125rem', marginBottom: '0.5rem' }}>No Approved Doctors Found</h3>
          <p style={{ color: 'var(--secondary-500)', fontSize: '0.875rem' }}>
            {searchTerm ? `No specialists match "${searchTerm}". Try another search term.` : 'No approved doctors available at the moment.'}
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-3 gap-6">
          {doctors.map((doc) => (
            <Card key={doc.id} hover className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div
                      style={{
                        width: '44px',
                        height: '44px',
                        borderRadius: '50%',
                        background: 'var(--primary-100)',
                        color: 'var(--primary-700)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 800,
                        fontSize: '1.125rem',
                      }}
                    >
                      {doc.user?.full_name ? doc.user.full_name.charAt(0) : 'D'}
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>
                        Dr. {doc.user?.full_name || 'Medical Specialist'}
                      </h3>
                      <div style={{ color: 'var(--primary-600)', fontSize: '0.875rem', fontWeight: 600 }}>
                        {doc.specialization}
                      </div>
                    </div>
                  </div>
                  <Badge variant="teal">Verified</Badge>
                </div>

                <p style={{ color: 'var(--secondary-600)', fontSize: '0.8125rem', lineHeight: 1.5, marginBottom: '1rem', minHeight: '38px' }}>
                  {doc.bio || 'Experienced medical practitioner providing personalized clinical consultation and care.'}
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', borderTop: '1px solid var(--secondary-200)', paddingTop: '0.75rem', marginBottom: '1.25rem', fontSize: '0.8125rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--secondary-700)' }}>
                    <Award size={16} color="var(--primary-600)" />
                    <span><strong>Experience:</strong> {doc.experience_years} years</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--secondary-700)' }}>
                    <Building size={16} color="var(--primary-600)" />
                    <span><strong>Affiliation:</strong> {doc.hospital_affiliation || 'CareAI Health Network'}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--secondary-700)' }}>
                    <DollarSign size={16} color="var(--accent-emerald)" />
                    <span><strong>Consultation Fee:</strong> {formatCurrency(doc.consultation_fee)}</span>
                  </div>
                </div>
              </div>

              <Button
                variant="primary"
                icon={Calendar}
                style={{ width: '100%', padding: '0.625rem' }}
                onClick={() => openBookingModal(doc)}
              >
                Book Appointment
              </Button>
            </Card>
          ))}
        </div>
      )}

      {/* Booking Modal */}
      {selectedDoctor && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '1rem',
          }}
        >
          <div
            className="animate-fade-in"
            style={{
              backgroundColor: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '540px',
              width: '100%',
              boxShadow: 'var(--shadow-xl)',
              overflow: 'hidden',
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '1.25rem 1.5rem',
                borderBottom: '1px solid var(--secondary-200)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'linear-gradient(135deg, var(--primary-50) 0%, #ffffff 100%)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <Calendar size={20} color="var(--primary-700)" />
                <div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Schedule Consultation</h3>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                    Dr. {selectedDoctor.user?.full_name} • {selectedDoctor.specialization}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedDoctor(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-400)', padding: '4px' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleBookAppointment} style={{ padding: '1.5rem' }}>
              {bookingSuccess ? (
                <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
                  <CheckCircle size={48} color="var(--accent-emerald)" style={{ marginBottom: '1rem' }} />
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--secondary-900)', marginBottom: '0.5rem' }}>
                    Appointment Request Submitted!
                  </h3>
                  <p style={{ color: 'var(--secondary-500)', fontSize: '0.875rem' }}>
                    Your consultation request has been sent to Dr. {selectedDoctor.user?.full_name}. Redirecting to your appointments...
                  </p>
                </div>
              ) : (
                <>
                  {bookingError && (
                    <div
                      style={{
                        background: '#fff1f2',
                        border: '1px solid #fecdd3',
                        color: '#9f1239',
                        padding: '0.75rem 1rem',
                        borderRadius: 'var(--radius-md)',
                        marginBottom: '1.25rem',
                        fontSize: '0.8125rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                      }}
                    >
                      <AlertCircle size={16} />
                      <span>{bookingError}</span>
                    </div>
                  )}

                  {/* Consultation Fee Banner */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid var(--secondary-200)', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
                    <span style={{ color: 'var(--secondary-600)' }}>Consultation Fee:</span>
                    <strong style={{ color: 'var(--primary-700)', fontSize: '1.125rem' }}>
                      {formatCurrency(selectedDoctor.consultation_fee)}
                    </strong>
                  </div>

                  {/* Date Picker */}
                  <div className="form-group">
                    <label className="form-label">Consultation Date *</label>
                    <input
                      type="date"
                      className="form-input"
                      required
                      min={new Date().toISOString().split('T')[0]}
                      value={bookingDate}
                      onChange={(e) => setBookingDate(e.target.value)}
                    />
                  </div>

                  {/* Dynamic Available Time Slot Picker */}
                  <div className="form-group">
                    <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>Available Time Slots *</span>
                      {loadingSlots && <span style={{ fontSize: '0.75rem', color: 'var(--primary-600)' }}>Checking live slots...</span>}
                    </label>

                    {loadingSlots ? (
                      <div style={{ padding: '1rem', textAlign: 'center', fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                        Loading available slots for {bookingDate}...
                      </div>
                    ) : availableSlots.length === 0 ? (
                      <div
                        style={{
                          padding: '1rem',
                          background: '#fffbeb',
                          border: '1px solid #fde68a',
                          borderRadius: '8px',
                          color: '#92400e',
                          fontSize: '0.8125rem',
                          textAlign: 'center',
                        }}
                      >
                        ⚠️ No available consultation slots for this date (the doctor may be off, on leave, or fully booked). Please select another date.
                      </div>
                    ) : (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', maxHeight: '180px', overflowY: 'auto', padding: '2px' }}>
                        {availableSlots.map((slot) => (
                          <button
                            key={slot}
                            type="button"
                            onClick={() => setBookingTime(slot)}
                            style={{
                              padding: '0.5rem',
                              borderRadius: 'var(--radius-sm)',
                              border: bookingTime === slot ? '2px solid var(--primary-600)' : '1px solid var(--secondary-200)',
                              background: bookingTime === slot ? 'var(--primary-50)' : '#ffffff',
                              color: bookingTime === slot ? 'var(--primary-800)' : 'var(--secondary-700)',
                              fontWeight: bookingTime === slot ? 700 : 500,
                              fontSize: '0.8125rem',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '4px',
                            }}
                          >
                            <Clock size={12} />
                            {slot}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Reason for Consultation */}
                  <div className="form-group">
                    <label className="form-label">Reason for Consultation *</label>
                    <input
                      type="text"
                      className="form-input"
                      required
                      placeholder="e.g. Chest pain, Follow-up consultation, Prescription renewal"
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                    />
                  </div>

                  {/* Patient Notes */}
                  <div className="form-group">
                    <label className="form-label">Additional Symptoms / Notes (Optional)</label>
                    <textarea
                      className="form-input"
                      rows={2}
                      placeholder="Describe any relevant symptoms, recent medications, or health concerns..."
                      value={patientNotes}
                      onChange={(e) => setPatientNotes(e.target.value)}
                    />
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                    <Button variant="secondary" onClick={() => setSelectedDoctor(null)} disabled={submitting}>
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant="primary"
                      disabled={submitting || availableSlots.length === 0 || !bookingTime}
                    >
                      {submitting ? 'Confirming Booking...' : 'Confirm & Request Consultation'}
                    </Button>
                  </div>
                </>
              )}
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default DoctorDirectoryPage;
