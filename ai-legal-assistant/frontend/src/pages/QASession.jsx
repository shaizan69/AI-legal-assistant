import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { MessageSquare, Send, Bot, User } from 'lucide-react';
import { qaAPI } from '../api/qa';

const QASession = () => {
  const { sessionId } = useParams();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);

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
      }
    })();
  }, [sessionId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: question,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');

    try {
      const res = await qaAPI.askQuestion(question, Number(sessionId));
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: res.answer || 'No answer returned.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (e) {
      console.error('Failed to ask question', e);
    }
  };

  return (
    <div className="qa-session">
      <div className="qa-header">
        <h1 className="qa-title">Q&A Session</h1>
        <p className="qa-subtitle">Ask questions about your document</p>
      </div>

      <div className="qa-container">
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-messages">
              <MessageSquare size={48} className="empty-icon" />
              <h3>Start a conversation</h3>
              <p>Ask questions about your document to get AI-powered insights.</p>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((message) => (
                <div key={message.id} className={`message ${message.type}`}>
                  <div className="message-avatar">
                    {message.type === 'user' ? <User size={20} /> : <Bot size={20} />}
                  </div>
                  <div className="message-content">
                    <div className="message-text">{message.content}</div>
                    <div className="message-time">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <form className="question-form" onSubmit={handleSubmit}>
          <div className="input-container">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question about the document..."
              className="question-input"
            />
            <button type="submit" className="send-button" disabled={!question.trim()}>
              <Send size={20} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default QASession;
