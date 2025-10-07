import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Send, Bot, User, Loader2, Copy, Check } from 'lucide-react';
import { qaAPI } from '../api/qa';
import './QASession.css';

const QASession = () => {
  const { sessionId } = useParams();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load existing questions for the session
    (async () => {
      try {
        const items = await qaAPI.getSessionQuestions(Number(sessionId));
        const mapped = items.map((q) => ([
          { id: `q-${q.id}`, type: 'user', content: q.question, timestamp: new Date(q.asked_at || q.created_at || Date.now()) },
          { id: `a-${q.id}`, type: 'ai', content: q.answer, timestamp: new Date(q.answered_at || Date.now()) }
        ])).flat().filter(m => m.content);
        setMessages(mapped);
      } catch(e) {
        console.error('Failed to load session messages', e);
        if (e.response?.status === 401) {
          console.log('Session expired, redirecting to login...');
          // Don't show error message for auth failures, let the interceptor handle it
        } else {
          // Show user-friendly error for other issues
          const errorMsg = {
            id: 'load-error',
            type: 'ai',
            content: 'Failed to load previous messages. Please refresh the page.',
            timestamp: new Date(),
          };
          setMessages([errorMsg]);
        }
      }
    })();
  }, [sessionId]);

  // Cleanup session when component unmounts
  useEffect(() => {
    return () => {
      // Clean up session and document when user navigates away
      if (sessionId) {
        // Add a small delay to ensure any pending operations complete
        setTimeout(() => {
          qaAPI.cleanupSession(Number(sessionId)).catch(error => {
            console.warn('Failed to cleanup session:', error);
          });
        }, 100);
      }
    };
  }, [sessionId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    const userQuestion = question.trim();
    
    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: userQuestion,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setIsLoading(true);
    
    // Add loading message
    const loadingMessage = {
      id: 'loading',
      type: 'ai',
      content: '🤔 Thinking... This may take up to 2 minutes for complex questions.',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      const res = await qaAPI.askQuestion(userQuestion, Number(sessionId));
      
      // Remove loading message and add actual response
      setMessages(prev => {
        const withoutLoading = prev.filter(msg => msg.id !== 'loading');
        const aiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: res.answer || 'No answer returned.',
          timestamp: new Date(),
        };
        return [...withoutLoading, aiMessage];
      });
    } catch (e) {
      console.error('Failed to ask question', e);
      let errorMessage = 'Sorry, I encountered an error while processing your question. Please try again.';
      
      if (e.code === 'ECONNABORTED' || e.message?.includes('timeout')) {
        errorMessage = 'The request timed out. The AI is taking longer than expected. Please try again with a simpler question.';
      } else if (e.response?.status === 401) {
        errorMessage = 'Your session has expired. Please refresh the page and login again.';
      } else if (e.response?.status === 500) {
        errorMessage = 'Server error. Please try again in a moment.';
      } else if (e.response?.status === 408) {
        errorMessage = 'Request timeout. The AI is taking too long to respond. Please try again.';
      }
      
      // Remove loading message and add error message
      setMessages(prev => {
        const withoutLoading = prev.filter(msg => msg.id !== 'loading');
        const errorMsg = {
          id: Date.now() + 1,
          type: 'ai',
          content: errorMessage,
          timestamp: new Date(),
          isError: true,
        };
        return [...withoutLoading, errorMsg];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e) => {
    setQuestion(e.target.value);
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleCleanup = async () => {
    try {
      await qaAPI.cleanupSession(Number(sessionId));
      alert('Session cleaned up successfully!');
    } catch (error) {
      console.error('Cleanup failed:', error);
      alert('Cleanup failed. Please try again.');
    }
  };

  const copyToClipboard = async (content, messageId) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-content">
          <div className="chat-title-section">
            <h1 className="chat-title">Document Q&A</h1>
            <p className="chat-subtitle">Ask questions about your document</p>
          </div>
          <div className="chat-actions">
            <button 
              className="cleanup-button"
              onClick={handleCleanup}
              title="Clean up session and document"
            >
              Clean Up
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <div className="empty-chat-content">
              <div className="empty-chat-icon">
                <Bot size={48} />
              </div>
              <h3 className="empty-chat-title">Start a conversation</h3>
              <p className="empty-chat-description">
                Ask questions about your document to get AI-powered insights and analysis.
              </p>
              <div className="suggested-questions">
                <p className="suggested-title">Try asking:</p>
                <div className="suggestion-chips">
                  <button 
                    className="suggestion-chip"
                    onClick={() => setQuestion("What are the main points of this document?")}
                  >
                    What are the main points of this document?
                  </button>
                  <button 
                    className="suggestion-chip"
                    onClick={() => setQuestion("Are there any risks or concerns mentioned?")}
                  >
                    Are there any risks or concerns mentioned?
                  </button>
                  <button 
                    className="suggestion-chip"
                    onClick={() => setQuestion("Can you summarize the key terms?")}
                  >
                    Can you summarize the key terms?
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((message) => (
              <div key={message.id} className={`message-wrapper ${message.type}`}>
                <div className="message">
                  <div className="message-avatar">
                    {message.type === 'user' ? (
                      <div className="user-avatar">
                        <User size={16} />
                      </div>
                    ) : (
                      <div className="ai-avatar">
                        <Bot size={16} />
                      </div>
                    )}
                  </div>
                  <div className="message-content">
                    <div className="message-header">
                      <span className="message-sender">
                        {message.type === 'user' ? 'You' : 'AI Assistant'}
                      </span>
                      <span className="message-time">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                    <div className={`message-text ${message.isError ? 'error-message' : ''}`}>
                      {message.content}
                    </div>
                    {message.type === 'ai' && (
                      <div className="message-actions">
                        <button
                          className="action-button"
                          onClick={() => copyToClipboard(message.content, message.id)}
                          title="Copy message"
                        >
                          {copiedMessageId === message.id ? (
                            <Check size={14} />
                          ) : (
                            <Copy size={14} />
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="message-wrapper ai">
                <div className="message">
                  <div className="message-avatar">
                    <div className="ai-avatar">
                      <Bot size={16} />
                    </div>
                  </div>
                  <div className="message-content">
                    <div className="message-header">
                      <span className="message-sender">AI Assistant</span>
                    </div>
                    <div className="typing-indicator">
                      <div className="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="chat-input-container">
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <div className="input-wrapper">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={handleTextareaChange}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about the document..."
              className="chat-input"
              rows="1"
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="send-button" 
              disabled={!question.trim() || isLoading}
              title="Send message"
            >
              {isLoading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <Send size={20} />
              )}
            </button>
          </div>
        </form>
        <div className="input-footer">
          <p className="input-hint">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
};

export default QASession;
