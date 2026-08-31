import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  Plus,
  Trash2,
  CheckCircle,
  AlertCircle,
  CalendarOff,
  Sun,
  Shield,
  Edit2,
  Sliders,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import doctorService from '../../services/doctorService';
import { formatDate } from '../../utils/formatters';

const DAYS = [
  { id: 0, name: 'Monday' },
  { id: 1, name: 'Tuesday' },
  { id: 2, name: 'Wednesday' },
  { id: 3, name: 'Thursday' },
  { id: 4, name: 'Friday' },
  { id: 5, name: 'Saturday' },
  { id: 6, name: 'Sunday' },
];

export function DoctorAvailabilityPage() {
  const [availabilities, setAvailabilities] = useState([]);
  const [unavailableDates, setUnavailableDates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // New Availability Form
  const [showAddModal, setShowAddModal] = useState(false);
  const [dayOfWeek, setDayOfWeek] = useState(0);
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('17:00');
  const [slotDuration, setSlotDuration] = useState(30);
  const [isActive, setIsActive] = useState(true);
  const [submittingAvail, setSubmittingAvail] = useState(false);

  // New Unavailable Date Form
  const [newLeaveDate, setNewLeaveDate] = useState('');
  const [newLeaveReason, setNewLeaveReason] = useState('');
  const [submittingLeave, setSubmittingLeave] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [availData, leaveData] = await Promise.all([
        doctorService.getMyAvailability().catch(() => []),
        doctorService.getMyUnavailableDates().catch(() => []),
      ]);
      setAvailabilities(availData || []);
      setUnavailableDates(leaveData || []);
    } catch (err) {
      console.error('Failed to load doctor schedule:', err);
      setErrorMessage('Failed to load schedule data.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAvailability = async (e) => {
    e.preventDefault();
    try {
      setSubmittingAvail(true);
      setErrorMessage(null);
      setActionMessage(null);

      const payload = {
        day_of_week: Number(dayOfWeek),
        start_time: startTime.length === 5 ? `${startTime}:00` : startTime,
        end_time: endTime.length === 5 ? `${endTime}:00` : endTime,
        slot_duration_minutes: Number(slotDuration),
        is_active: isActive,
      };

      await doctorService.createAvailability(payload);
      setActionMessage('Availability schedule rule successfully added!');
      setShowAddModal(false);
      loadData();
    } catch (err) {
      console.error('Failed to add availability:', err);
      setErrorMessage(err.message || 'Failed to add availability schedule.');
    } finally {
      setSubmittingAvail(false);
    }
  };

  const handleDeleteAvailability = async (id) => {
    if (!window.confirm('Are you sure you want to remove this working schedule?')) return;
    try {
      await doctorService.deleteAvailability(id);
      setActionMessage('Working schedule removed.');
      loadData();
    } catch (err) {
      console.error('Failed to delete availability:', err);
      setErrorMessage(err.message || 'Failed to remove schedule.');
    }
  };

  const handleAddUnavailableDate = async (e) => {
    e.preventDefault();
    if (!newLeaveDate) return;
    try {
      setSubmittingLeave(true);
      setErrorMessage(null);
      setActionMessage(null);

      await doctorService.addUnavailableDate({
        unavailable_date: newLeaveDate,
        reason: newLeaveReason.trim() || 'Personal absence / Leave',
      });

      setActionMessage(`Marked ${newLeaveDate} as unavailable.`);
      setNewLeaveDate('');
      setNewLeaveReason('');
      loadData();
    } catch (err) {
      console.error('Failed to add unavailable date:', err);
      setErrorMessage(err.message || 'Failed to record absence date.');
    } finally {
      setSubmittingLeave(false);
    }
  };

  const handleDeleteUnavailableDate = async (id) => {
    try {
      await doctorService.deleteUnavailableDate(id);
      setActionMessage('Unblocked calendar date.');
      loadData();
    } catch (err) {
      console.error('Failed to remove unavailable date:', err);
      setErrorMessage(err.message || 'Failed to remove leave date.');
    }
  };

  // Group availability by day of week
  const availabilitiesByDay = DAYS.map((day) => ({
    ...day,
    schedules: availabilities.filter((a) => a.day_of_week === day.id),
  }));

  return (
    <div className="animate-fade-in" style={{ maxWidth: '1080px', margin: '0 auto', paddingBottom: '3rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
          <Calendar size={28} color="var(--primary-700)" />
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800 }}>Schedule & Availability Management</h1>
        </div>
        <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
          Configure your weekly consultation working hours, appointment slot durations, and planned leaves. Patient bookings are dynamically validated against these schedules.
        </p>
      </div>

      {actionMessage && (
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
          <span>{actionMessage}</span>
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

      {/* Two Column Layout: Weekly Schedule & Unavailable Dates */}
      <div className="grid grid-cols-3 gap-6">
        {/* Left 2 Cols: Weekly Working Hours */}
        <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <Card
            title="Weekly Consultation Schedule"
            subtitle="Recurring weekly consultation hours and appointment durations"
            headerAction={
              <Button
                variant="primary"
                icon={Plus}
                style={{ padding: '0.4rem 0.875rem', fontSize: '0.8125rem' }}
                onClick={() => setShowAddModal(true)}
              >
                Add Schedule Window
              </Button>
            }
          >
            {loading ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
                Loading working hours...
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                {availabilitiesByDay.map((day) => (
                  <div
                    key={day.id}
                    style={{
                      background: day.schedules.length > 0 ? '#ffffff' : '#f8fafc',
                      border: '1px solid var(--secondary-200)',
                      borderRadius: 'var(--radius-md)',
                      padding: '0.875rem 1rem',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: '0.75rem',
                    }}
                  >
                    <div style={{ minWidth: '120px' }}>
                      <strong style={{ fontSize: '0.9375rem', color: day.schedules.length > 0 ? 'var(--secondary-900)' : 'var(--secondary-500)' }}>
                        {day.name}
                      </strong>
                      <div style={{ fontSize: '0.75rem', color: 'var(--secondary-400)' }}>
                        {day.schedules.length > 0 ? `${day.schedules.length} active window(s)` : 'Off / No consultations'}
                      </div>
                    </div>

                    <div style={{ flex: 1, display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {day.schedules.length > 0 ? (
                        day.schedules.map((sched) => (
                          <div
                            key={sched.id}
                            style={{
                              background: 'var(--primary-50)',
                              border: '1px solid var(--primary-200)',
                              color: 'var(--primary-900)',
                              padding: '0.4rem 0.75rem',
                              borderRadius: '8px',
                              fontSize: '0.8125rem',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.5rem',
                            }}
                          >
                            <Clock size={14} color="var(--primary-700)" />
                            <span>
                              <strong>{sched.start_time.substring(0, 5)} - {sched.end_time.substring(0, 5)}</strong>
                              <span style={{ fontSize: '0.6875rem', color: 'var(--primary-600)', marginLeft: '4px' }}>
                                ({sched.slot_duration_minutes}m slots)
                              </span>
                            </span>
                            <button
                              type="button"
                              onClick={() => handleDeleteAvailability(sched.id)}
                              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent-rose)', padding: 0 }}
                              title="Delete window"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        ))
                      ) : (
                        <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-400)', fontStyle: 'italic' }}>
                          No hours scheduled
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right 1 Col: Time-Off & Unavailable Dates */}
        <div>
          <Card
            title="Time-Off & Leaves"
            subtitle="Block dates when you are unavailable"
          >
            {/* Add Unavailable Date Form */}
            <form onSubmit={handleAddUnavailableDate} style={{ marginBottom: '1.25rem' }}>
              <div className="form-group">
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Select Date to Block *</label>
                <input
                  type="date"
                  className="form-input"
                  required
                  min={new Date().toISOString().split('T')[0]}
                  value={newLeaveDate}
                  onChange={(e) => setNewLeaveDate(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label" style={{ fontSize: '0.75rem' }}>Reason (Optional)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Medical Conference, Annual Leave"
                  value={newLeaveReason}
                  onChange={(e) => setNewLeaveReason(e.target.value)}
                />
              </div>

              <Button
                type="submit"
                variant="secondary"
                icon={CalendarOff}
                disabled={submittingLeave || !newLeaveDate}
                style={{ width: '100%', fontSize: '0.8125rem' }}
              >
                {submittingLeave ? 'Blocking Date...' : 'Block Date from Booking'}
              </Button>
            </form>

            {/* List of Blocked Dates */}
            <div style={{ borderTop: '1px solid var(--secondary-200)', paddingTop: '1rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Upcoming Blocked Dates ({unavailableDates.length})
              </div>

              {unavailableDates.length === 0 ? (
                <p style={{ fontSize: '0.8125rem', color: 'var(--secondary-400)', fontStyle: 'italic', margin: 0 }}>
                  No planned absences.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '280px', overflowY: 'auto' }}>
                  {unavailableDates.map((leave) => (
                    <div
                      key={leave.id}
                      style={{
                        background: '#fff1f2',
                        border: '1px solid #fecdd3',
                        borderRadius: '6px',
                        padding: '0.5rem 0.75rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '0.8125rem',
                      }}
                    >
                      <div>
                        <strong style={{ color: '#9f1239' }}>{formatDate(leave.unavailable_date)}</strong>
                        <div style={{ fontSize: '0.6875rem', color: '#881337' }}>{leave.reason || 'Unavailable'}</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDeleteUnavailableDate(leave.id)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent-rose)', padding: '2px' }}
                        title="Unblock date"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Add Availability Modal */}
      {showAddModal && (
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
              maxWidth: '480px',
              width: '100%',
              boxShadow: 'var(--shadow-xl)',
              overflow: 'hidden',
              padding: '1.5rem',
            }}
          >
            <h3 style={{ fontSize: '1.125rem', fontWeight: 800, marginBottom: '0.25rem' }}>
              Add Weekly Availability Window
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)', marginBottom: '1.25rem' }}>
              Set working hours and appointment slot duration for a day of the week.
            </p>

            <form onSubmit={handleCreateAvailability}>
              <div className="form-group">
                <label className="form-label">Day of Week *</label>
                <select
                  className="form-input"
                  value={dayOfWeek}
                  onChange={(e) => setDayOfWeek(Number(e.target.value))}
                >
                  {DAYS.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3" style={{ marginBottom: '1rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Start Time *</label>
                  <input
                    type="time"
                    className="form-input"
                    required
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                  />
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">End Time *</label>
                  <input
                    type="time"
                    className="form-input"
                    required
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Consultation Slot Duration</label>
                <select
                  className="form-input"
                  value={slotDuration}
                  onChange={(e) => setSlotDuration(Number(e.target.value))}
                >
                  <option value={15}>15 minutes</option>
                  <option value={20}>20 minutes</option>
                  <option value={30}>30 minutes (Standard)</option>
                  <option value={45}>45 minutes</option>
                  <option value={60}>60 minutes (Comprehensive)</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                <Button variant="secondary" onClick={() => setShowAddModal(false)} disabled={submittingAvail}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={submittingAvail}>
                  {submittingAvail ? 'Saving Window...' : 'Save Availability'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default DoctorAvailabilityPage;
