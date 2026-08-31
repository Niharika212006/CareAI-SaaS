import React, { useState, useEffect, useRef, useCallback } from 'react';
import useAuth from '../../hooks/useAuth';
import aiAssistantService from '../../services/aiAssistantService';
import AIAssistantHeader from './AIAssistantHeader';
import ConversationSidebar from './ConversationSidebar';
import EmptyConversationState from './EmptyConversationState';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import AILoadingIndicator from './AILoadingIndicator';
import AIErrorState from './AIErrorState';

export function AIAssistantChat({ isOpen, onClose }) {
  const { role } = useAuth();

  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);
  const [lastUserMessage, setLastUserMessage] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const messagesEndRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Fetch list of user conversations
  const fetchConversations = useCallback(async () => {
    try {
      setIsLoadingConversations(true);
      const res = await aiAssistantService.getConversations();
      setConversations(res || []);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setIsLoadingConversations(false);
    }
  }, []);

  // Load conversation threads on open
  useEffect(() => {
    if (isOpen) {
      fetchConversations();
    }
  }, [isOpen, fetchConversations]);

  // Fetch message turns when activeConversationId changes
  useEffect(() => {
    if (!activeConversationId) {
      setMessages([]);
      return;
    }

    async function loadThread() {
      try {
        setIsLoadingMessages(true);
        setError(null);
        const thread = await aiAssistantService.getConversation(activeConversationId);
        setMessages(thread.messages || []);
      } catch (err) {
        console.error('Failed to load conversation thread:', err);
        setError('Failed to load conversation history. Please try again.');
      } finally {
        setIsLoadingMessages(false);
      }
    }

    loadThread();
  }, [activeConversationId]);

  // Scroll to bottom when messages or loading state changes
  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending, scrollToBottom]);

  // Handler: Start New Conversation
  const handleNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setError(null);
    setLastUserMessage(null);
  };

  // Handler: Select Existing Thread
  const handleSelectConversation = (convId) => {
    if (convId === activeConversationId) return;
    setActiveConversationId(convId);
    setError(null);
    setLastUserMessage(null);
  };

  // Handler: Delete Conversation
  const handleDeleteConversation = async (convId) => {
    try {
      await aiAssistantService.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConversationId === convId) {
        handleNewConversation();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
      setError('Could not delete conversation. Please try again.');
    }
  };

  // Handler: Send Message
  const handleSendMessage = async (userText) => {
    if (!userText.trim() || isSending) return;

    setError(null);
    setLastUserMessage(userText);

    // Optimistically display the user's message
    const tempUserMsg = {
      id: Date.now(),
      conversation_id: activeConversationId || 0,
      sender: 'USER',
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsSending(true);

    try {
      const response = await aiAssistantService.sendMessage(userText, activeConversationId);

      // Assistant turn received
      const assistantMsg = {
        id: Date.now() + 1,
        conversation_id: response.conversation_id,
        sender: 'ASSISTANT',
        content: response.assistant_response,
        model_name: response.model_name,
        created_at: response.created_at,
        safety_metadata: response.safety_metadata,
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // If this was a new conversation, set active ID and refresh sidebar
      if (!activeConversationId && response.conversation_id) {
        setActiveConversationId(response.conversation_id);
        fetchConversations();
      }
    } catch (err) {
      console.error('AI Assistant chat error:', err);
      setError(err);
    } finally {
      setIsSending(false);
    }
  };

  // Handler: Retry Last Message
  const handleRetry = () => {
    if (lastUserMessage) {
      // Remove last failed temporary message if needed and re-send
      handleSendMessage(lastUserMessage);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.45)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
      className="animate-fade-in"
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '1040px',
          height: '85vh',
          maxHeight: '820px',
          backgroundColor: 'var(--bg-main)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 20px 45px -10px rgba(15, 23, 42, 0.3)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          border: '1px solid var(--secondary-200)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <AIAssistantHeader
          role={role}
          onClose={onClose}
          onNewConversation={handleNewConversation}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        />

        {/* Body (Sidebar + Chat Arena) */}
        <div style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden' }}>
          {/* Collapsible Conversation History Sidebar */}
          {isSidebarOpen && (
            <ConversationSidebar
              conversations={conversations}
              activeConversationId={activeConversationId}
              onSelectConversation={handleSelectConversation}
              onNewConversation={handleNewConversation}
              onDeleteConversation={handleDeleteConversation}
              isLoading={isLoadingConversations}
            />
          )}

          {/* Main Chat Area */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              minWidth: 0,
              backgroundColor: 'var(--bg-main)',
            }}
          >
            {/* Messages Scroll Area */}
            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '1.25rem 1.5rem',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              {messages.length === 0 && !isLoadingMessages && !isSending ? (
                <EmptyConversationState role={role} onSelectPrompt={handleSendMessage} />
              ) : (
                <>
                  {messages.map((msg, index) => (
                    <ChatMessage
                      key={msg.id || index}
                      message={msg}
                      isLastTurn={index === messages.length - 1}
                    />
                  ))}

                  {isSending && <AILoadingIndicator />}

                  {error && <AIErrorState error={error} onRetry={handleRetry} />}
                </>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Box */}
            <ChatInput onSendMessage={handleSendMessage} isSending={isSending} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default AIAssistantChat;
