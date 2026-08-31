import React, { useState } from 'react';
import { MessageSquare, Plus, Trash2, Clock, Check, X, Loader2 } from 'lucide-react';

export function ConversationSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isLoading,
}) {
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteClick = (e, convId) => {
    e.stopPropagation();
    setDeleteConfirmId(convId);
  };

  const handleConfirmDelete = async (e, convId) => {
    e.stopPropagation();
    try {
      setIsDeleting(true);
      await onDeleteConversation(convId);
    } finally {
      setIsDeleting(false);
      setDeleteConfirmId(null);
    }
  };

  const handleCancelDelete = (e) => {
    e.stopPropagation();
    setDeleteConfirmId(null);
  };

  return (
    <div
      style={{
        width: '260px',
        borderRight: '1px solid var(--secondary-200)',
        background: '#ffffff',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        flexShrink: 0,
      }}
      className="conversation-sidebar"
    >
      {/* Sidebar Action Bar */}
      <div style={{ padding: '0.875rem 1rem', borderBottom: '1px solid var(--secondary-200)' }}>
        <button
          type="button"
          onClick={onNewConversation}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            background: 'linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%)',
            color: '#ffffff',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            padding: '0.625rem 1rem',
            fontSize: '0.8125rem',
            fontWeight: 700,
            cursor: 'pointer',
            boxShadow: '0 2px 6px rgba(13, 148, 136, 0.25)',
            transition: 'all 0.15s ease',
          }}
        >
          <Plus size={16} /> New Conversation
        </button>
      </div>

      {/* Threads List */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.25rem',
        }}
      >
        {isLoading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem 0', color: 'var(--secondary-500)' }}>
            <Loader2 size={20} className="animate-spin" />
          </div>
        ) : conversations.length === 0 ? (
          <div
            style={{
              padding: '2rem 1rem',
              textAlign: 'center',
              color: 'var(--secondary-500)',
              fontSize: '0.8125rem',
            }}
          >
            <MessageSquare size={24} style={{ margin: '0 auto 0.5rem auto', opacity: 0.4 }} />
            <div>No previous chats yet.</div>
            <div style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>Start a new conversation!</div>
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = activeConversationId === conv.id;
            const isConfirming = deleteConfirmId === conv.id;

            return (
              <div
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                style={{
                  padding: '0.625rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  background: isActive ? 'var(--primary-50)' : 'transparent',
                  border: isActive ? '1px solid var(--primary-200)' : '1px solid transparent',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '0.5rem',
                  transition: 'background 0.15s ease',
                }}
                className="conversation-item"
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: 0, flex: 1 }}>
                  <MessageSquare
                    size={15}
                    style={{
                      color: isActive ? 'var(--primary-600)' : 'var(--secondary-500)',
                      flexShrink: 0,
                    }}
                  />
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div
                      style={{
                        fontSize: '0.8125rem',
                        fontWeight: isActive ? 700 : 500,
                        color: isActive ? 'var(--primary-900)' : 'var(--secondary-800)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                      title={conv.title}
                    >
                      {conv.title || 'Untitled Conversation'}
                    </div>
                    {conv.last_message_preview && (
                      <div
                        style={{
                          fontSize: '0.6875rem',
                          color: 'var(--secondary-500)',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          marginTop: '2px',
                        }}
                      >
                        {conv.last_message_preview}
                      </div>
                    )}
                  </div>
                </div>

                {/* Delete / Confirm Actions */}
                {isConfirming ? (
                  <div
                    style={{ display: 'flex', alignItems: 'center', gap: '2px', flexShrink: 0 }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      type="button"
                      disabled={isDeleting}
                      onClick={(e) => handleConfirmDelete(e, conv.id)}
                      style={{
                        background: '#fee2e2',
                        color: '#dc2626',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '3px',
                        cursor: 'pointer',
                      }}
                      title="Confirm Delete"
                    >
                      {isDeleting ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />}
                    </button>
                    <button
                      type="button"
                      onClick={handleCancelDelete}
                      style={{
                        background: 'var(--secondary-200)',
                        color: 'var(--secondary-700)',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '3px',
                        cursor: 'pointer',
                      }}
                      title="Cancel"
                    >
                      <X size={13} />
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={(e) => handleDeleteClick(e, conv.id)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--secondary-400)',
                      cursor: 'pointer',
                      padding: '4px',
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      opacity: 0.7,
                      transition: 'opacity 0.15s ease, color 0.15s ease',
                      flexShrink: 0,
                    }}
                    className="delete-conv-btn"
                    title="Delete Conversation"
                  >
                    <Trash2 size={13} />
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default ConversationSidebar;
