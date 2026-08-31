import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Bell,
  Check,
  CheckCheck,
  Calendar,
  FileText,
  ShieldCheck,
  AlertTriangle,
  Info,
  Clock,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import notificationService from '../../services/notificationService';
import { formatDateTime } from '../../utils/formatters';

export function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const dropdownRef = useRef(null);

  // Poll unread count on mount and periodically
  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 20000); // 20s polling
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const data = await notificationService.getUnreadCount();
      setUnreadCount(data.unread_count || 0);
    } catch {
      // Quiet fail on network hiccup
    }
  };

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await notificationService.getNotifications({ limit: 8 });
      setNotifications(data.items || []);
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      console.error('Failed to load notifications:', err);
      setError('Unable to fetch notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    if (!isOpen) {
      fetchNotifications();
    }
    setIsOpen(!isOpen);
  };

  const handleMarkRead = async (e, id) => {
    e.stopPropagation();
    try {
      await notificationService.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Mark read failed:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Mark all read failed:', err);
    }
  };

  const getTypeIcon = (type, priority) => {
    if (priority === 'CRITICAL' || priority === 'HIGH') {
      return <AlertTriangle size={15} color="var(--accent-rose)" />;
    }
    switch (type) {
      case 'APPOINTMENT':
        return <Calendar size={15} color="var(--primary-600)" />;
      case 'PRESCRIPTION':
        return <FileText size={15} color="var(--accent-blue)" />;
      case 'DOCTOR_APPROVAL':
        return <ShieldCheck size={15} color="var(--accent-green)" />;
      case 'AI_SAFETY':
        return <Sparkles size={15} color="var(--accent-amber)" />;
      default:
        return <Info size={15} color="var(--secondary-500)" />;
    }
  };

  return (
    <div style={{ position: 'relative' }} ref={dropdownRef}>
      {/* Bell Trigger Button */}
      <button
        onClick={handleToggle}
        aria-label="Notifications"
        style={{
          position: 'relative',
          padding: '0.5rem',
          borderRadius: 'var(--radius-md)',
          background: isOpen ? 'var(--secondary-100)' : '#ffffff',
          border: '1px solid var(--secondary-200)',
          color: 'var(--secondary-700)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.15s ease',
        }}
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span
            style={{
              position: 'absolute',
              top: '-4px',
              right: '-4px',
              background: 'var(--accent-rose)',
              color: '#ffffff',
              fontSize: '0.6875rem',
              fontWeight: 800,
              minWidth: '18px',
              height: '18px',
              borderRadius: '9px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0 4px',
              border: '2px solid #ffffff',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            }}
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Floating Notification Panel Dropdown */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            right: 0,
            top: 'calc(100% + 8px)',
            width: '360px',
            maxWidth: '90vw',
            backgroundColor: '#ffffff',
            borderRadius: 'var(--radius-lg)',
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05)',
            border: '1px solid var(--secondary-200)',
            zIndex: 100,
            overflow: 'hidden',
          }}
          className="animate-fade-in"
        >
          {/* Header */}
          <div
            style={{
              padding: '0.875rem 1rem',
              borderBottom: '1px solid var(--secondary-100)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              background: 'var(--secondary-50)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--secondary-900)' }}>
                Notifications
              </span>
              {unreadCount > 0 && (
                <span
                  style={{
                    fontSize: '0.6875rem',
                    background: 'var(--primary-100)',
                    color: 'var(--primary-700)',
                    padding: '0.125rem 0.5rem',
                    borderRadius: '10px',
                    fontWeight: 700,
                  }}
                >
                  {unreadCount} new
                </span>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--primary-600)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                }}
              >
                <CheckCheck size={14} /> Mark all read
              </button>
            )}
          </div>

          {/* Notification List Container */}
          <div style={{ maxHeight: '380px', overflowY: 'auto' }}>
            {loading ? (
              <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--secondary-500)', fontSize: '0.8125rem' }}>
                Loading alerts...
              </div>
            ) : error ? (
              <div style={{ padding: '1.5rem 1rem', textAlign: 'center', color: 'var(--accent-rose)', fontSize: '0.8125rem' }}>
                {error}
              </div>
            ) : notifications.length === 0 ? (
              <div style={{ padding: '2.5rem 1rem', textAlign: 'center', color: 'var(--secondary-400)' }}>
                <Bell size={28} style={{ margin: '0 auto 0.5rem auto', opacity: 0.5 }} />
                <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--secondary-700)' }}>
                  No notifications yet
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--secondary-400)', marginTop: '2px' }}>
                  We will notify you about appointments and safety updates.
                </div>
              </div>
            ) : (
              <div>
                {notifications.map((notif) => (
                  <div
                    key={notif.id}
                    style={{
                      padding: '0.75rem 1rem',
                      borderBottom: '1px solid var(--secondary-100)',
                      backgroundColor: notif.is_read ? '#ffffff' : '#f0f9ff',
                      display: 'flex',
                      gap: '0.75rem',
                      alignItems: 'flex-start',
                      transition: 'background-color 0.15s ease',
                      position: 'relative',
                    }}
                  >
                    {/* Category Icon */}
                    <div
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '6px',
                        backgroundColor: notif.is_read ? 'var(--secondary-100)' : 'var(--primary-100)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        marginTop: '2px',
                      }}
                    >
                      {getTypeIcon(notif.notification_type, notif.priority)}
                    </div>

                    {/* Notification Body */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                        <strong style={{ fontSize: '0.8125rem', color: 'var(--secondary-900)' }}>
                          {notif.title}
                        </strong>
                        <span style={{ fontSize: '0.6875rem', color: 'var(--secondary-400)', whiteSpace: 'nowrap', marginLeft: '6px' }}>
                          {formatDateTime(notif.created_at)}
                        </span>
                      </div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--secondary-600)', margin: 0, lineHeight: 1.4 }}>
                        {notif.message}
                      </p>
                    </div>

                    {/* Single Mark Read Action */}
                    {!notif.is_read && (
                      <button
                        onClick={(e) => handleMarkRead(e, notif.id)}
                        title="Mark as read"
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: 'var(--primary-600)',
                          cursor: 'pointer',
                          padding: '2px',
                          display: 'flex',
                          alignItems: 'center',
                          marginTop: '2px',
                        }}
                      >
                        <Check size={14} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer View All Link */}
          <div
            style={{
              padding: '0.625rem 1rem',
              borderTop: '1px solid var(--secondary-100)',
              textAlign: 'center',
              backgroundColor: '#ffffff',
            }}
          >
            <Link
              to="/notifications"
              onClick={() => setIsOpen(false)}
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--primary-600)',
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              View all notifications <ExternalLink size={12} />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

export default NotificationBell;
