import React, { useState, useEffect } from 'react';
import {
  Bell,
  Check,
  CheckCheck,
  Trash2,
  Calendar,
  FileText,
  ShieldCheck,
  AlertTriangle,
  Info,
  Sparkles,
  Filter,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import notificationService from '../../services/notificationService';
import { formatDateTime } from '../../utils/formatters';

export function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('ALL'); // 'ALL', 'UNREAD', 'APPOINTMENT', 'PRESCRIPTION', 'AI_SAFETY'
  const [actionMessage, setActionMessage] = useState(null);

  useEffect(() => {
    loadNotifications();
  }, [activeTab]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = { limit: 50 };
      if (activeTab === 'UNREAD') {
        params.unread_only = true;
      }
      const data = await notificationService.getNotifications(params);
      let items = data.items || [];
      if (activeTab !== 'ALL' && activeTab !== 'UNREAD') {
        items = items.filter((n) => n.notification_type === activeTab);
      }
      setNotifications(items);
      setTotalCount(data.total || 0);
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      console.error('Failed to load notifications page:', err);
      setError(err.message || 'Failed to load notifications.');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (id) => {
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
      setActionMessage('All notifications marked as read.');
      setTimeout(() => setActionMessage(null), 3000);
    } catch (err) {
      console.error('Mark all read failed:', err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await notificationService.deleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setTotalCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Delete notification failed:', err);
    }
  };

  const getTypeIcon = (type, priority) => {
    if (priority === 'CRITICAL' || priority === 'HIGH') {
      return <AlertTriangle size={18} color="var(--accent-rose)" />;
    }
    switch (type) {
      case 'APPOINTMENT':
        return <Calendar size={18} color="var(--primary-600)" />;
      case 'PRESCRIPTION':
        return <FileText size={18} color="var(--accent-blue)" />;
      case 'DOCTOR_APPROVAL':
        return <ShieldCheck size={18} color="var(--accent-green)" />;
      case 'AI_SAFETY':
        return <Sparkles size={18} color="var(--accent-amber)" />;
      default:
        return <Info size={18} color="var(--secondary-500)" />;
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'CRITICAL':
        return <Badge variant="rose">Critical Alert</Badge>;
      case 'HIGH':
        return <Badge variant="amber">High Priority</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
            <h1 style={{ fontSize: '1.875rem' }}>Notification Center</h1>
            {unreadCount > 0 && (
              <Badge variant="rose">{unreadCount} Unread</Badge>
            )}
          </div>
          <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
            In-app smart alerts, consultation updates, prescription arrivals, and AI clinical safety reports.
          </p>
        </div>

        {unreadCount > 0 && (
          <Button variant="secondary" icon={CheckCheck} onClick={handleMarkAllRead}>
            Mark all as read
          </Button>
        )}
      </div>

      {actionMessage && (
        <div
          style={{
            background: '#dcfce7',
            border: '1px solid #bbf7d0',
            color: '#15803d',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <Check size={16} />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {[
          { id: 'ALL', label: 'All Notifications' },
          { id: 'UNREAD', label: `Unread (${unreadCount})` },
          { id: 'APPOINTMENT', label: 'Appointments' },
          { id: 'PRESCRIPTION', label: 'Prescriptions' },
          { id: 'AI_SAFETY', label: 'AI Safety' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '0.4rem 0.875rem',
              borderRadius: '6px',
              border: activeTab === tab.id ? '1px solid var(--primary-600)' : '1px solid var(--secondary-200)',
              background: activeTab === tab.id ? 'var(--primary-50)' : '#ffffff',
              color: activeTab === tab.id ? 'var(--primary-800)' : 'var(--secondary-600)',
              fontWeight: activeTab === tab.id ? 700 : 500,
              fontSize: '0.8125rem',
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Notification List Card */}
      <Card>
        {loading ? (
          <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            Loading notification feed...
          </div>
        ) : error ? (
          <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--accent-rose)' }}>
            {error}
          </div>
        ) : notifications.length === 0 ? (
          <div style={{ padding: '3.5rem 1rem', textAlign: 'center', background: '#f8fafc', borderRadius: '8px', border: '1px dashed var(--secondary-200)' }}>
            <Bell size={36} color="var(--secondary-400)" style={{ margin: '0 auto 0.75rem auto' }} />
            <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '0.25rem' }}>No Notifications Found</div>
            <p style={{ color: 'var(--secondary-500)', fontSize: '0.8125rem' }}>
              You have no active alerts in this category.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {notifications.map((notif) => (
              <div
                key={notif.id}
                style={{
                  padding: '1rem 1.25rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--secondary-200)',
                  backgroundColor: notif.is_read ? '#ffffff' : '#f0f9ff',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: '1rem',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', flex: 1 }}>
                  <div
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '8px',
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

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '4px', flexWrap: 'wrap' }}>
                      <strong style={{ fontSize: '0.9375rem', color: 'var(--secondary-900)' }}>
                        {notif.title}
                      </strong>
                      {getPriorityBadge(notif.priority)}
                      {!notif.is_read && (
                        <span
                          style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            backgroundColor: 'var(--primary-600)',
                            display: 'inline-block',
                          }}
                        />
                      )}
                    </div>
                    <p style={{ color: 'var(--secondary-700)', fontSize: '0.8125rem', margin: '0 0 6px 0', lineHeight: 1.5 }}>
                      {notif.message}
                    </p>
                    <div style={{ fontSize: '0.75rem', color: 'var(--secondary-400)' }}>
                      {formatDateTime(notif.created_at)}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {!notif.is_read && (
                    <Button
                      variant="secondary"
                      style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                      icon={Check}
                      onClick={() => handleMarkRead(notif.id)}
                    >
                      Mark read
                    </Button>
                  )}
                  <button
                    onClick={() => handleDelete(notif.id)}
                    title="Delete notification"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--secondary-400)',
                      cursor: 'pointer',
                      padding: '0.35rem',
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

export default NotificationsPage;
